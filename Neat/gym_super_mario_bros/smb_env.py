"""An OpenAI Gym environment for Super Mario Bros. and Lost Levels."""
from collections import defaultdict
from nes_py import NESEnv
import math
import numpy as np
from ._roms import decode_target
from ._roms import rom_path


# create a dictionary mapping value of status register to string names
_STATUS_MAP = defaultdict(lambda: 'fireball', {0:'small', 1: 'tall'})


# a set of state values indicating that Mario is "busy"
_BUSY_STATES = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x07]


# RAM addresses for enemy types on the screen
_ENEMY_TYPE_ADDRESSES = [0x0016, 0x0017, 0x0018, 0x0019, 0x001A]

#RAM addresses for enemy x positions on screen
_ENEMY_X_ADDRESSES = [0x0087,0x0088, 0x0089, 0x008A, 0x008B]

#RAM addresses for enemy y values - two addresses, multiply together for global y
_ENEMY_Y_ADDRESSES_1 = [0x00B6, 0x00B7, 0x00B8, 0x00B9, 0x00BA]
_ENEMY_Y_ADDRESSES_2 = [0x00CF, 0x00D0, 0x00D1, 0x00D2, 0x00D3]

#RAM addresses for powerup x position - add two together
_POWERUP_X_ADDRESS = 0x008C
_SCREEN_PAGE_SHIFT = 0x006D

#RAM addresses for powerup y position - add two together
_POWERUP_Y_ADDRESS_1 = 0x00BB
_POWERUP_Y_ADDRESS_2 = 0x00D4


# enemies whose context indicate that a stage change will occur (opposed to an
# enemy that implies a stage change wont occur -- i.e., a vine)
# Bowser = 0x2D
# Flagpole = 0x31
_STAGE_OVER_ENEMIES = np.array([0x2D, 0x31])


class idHolder:
    def __init__(self,id):
        self.id = id;
class SuperMarioBrosEnv(NESEnv):
    """An environment for playing Super Mario Bros with OpenAI Gym."""

    # the legal range of rewards for each step
    reward_range = (-15, 15)

    def __init__(self, window_name=None,rom_mode='vanilla', lost_levels=False, target=None):
        """
        Initialize a new Super Mario Bros environment.

        Args:
            rom_mode (str): the ROM mode to use when loading ROMs from disk
            lost_levels (bool): whether to load the ROM with lost levels.
                - False: load original Super Mario Bros.
                - True: load Super Mario Bros. Lost Levels
            target (tuple): a tuple of the (world, stage) to play as a level

        Returns:
            None

        """

        #set gym spec id if given
        if (window_name is not None):
            self.spec = {'id':window_name};
        # decode the ROM path based on mode and lost levels flag
        rom = rom_path(lost_levels, rom_mode)
        # initialize the super object with the ROM path
        super(SuperMarioBrosEnv, self).__init__(rom)
        # set the target world, stage, and area variables
        target = decode_target(target, lost_levels)
        self._target_world, self._target_stage, self._target_area = target
        # setup a variable to keep track of the last frames time
        self._time_last = 0
        # setup a variable to keep track of the last frames x position
        self._x_position_last = 0
        self._stillness_frame_count = 0;
        self._max_x = 0;
        self._last_area = 0;
        self._last_stage = 0;
        self._last_level = 0;
        # reset the emulator
        self.reset()
        # skip the start screen
        self._skip_start_screen()
        # set lives to 0
        self.ram[0x075a] = 0
        # create a backup state to restore from on subsequent calls to reset
        self._backup()

    def setWindowName(self,name):
        self.spec = idHolder(name);
        
        
    @property
    def is_single_stage_env(self):
        """Return True if this environment is a stage environment."""
        return self._target_world is not None and self._target_area is not None

    # MARK: Memory access

    def _read_mem_range(self, address, length):
        """
        Read a range of bytes where each byte is a 10's place figure.

        Args:
            address (int): the address to read from as a 16 bit integer
            length: the number of sequential bytes to read

        Note:
            this method is specific to Mario where three GUI values are stored
            in independent memory slots to save processing time
            - score has 6 10's places
            - coins has 2 10's places
            - time has 3 10's places

        Returns:
            the integer value of this 10's place representation

        """
        return int(''.join(map(str, self.ram[address:address + length])))
    
    @property
    def _level(self):
        """Return the level of the game."""
        return self.ram[0x075f] * 4 + self.ram[0x075c]

    @property
    def _world(self):
        """Return the current world (1 to 8)."""
        return self.ram[0x075f] + 1

    @property
    def _stage(self):
        """Return the current stage (1 to 4)."""
        return self.ram[0x075c] + 1

    @property
    def _area(self):
        """Return the current area number (1 to 5)."""
        return self.ram[0x0760] + 1

    @property
    def _score(self):
        """Return the current player score (0 to 999990)."""
        # score is represented as a figure with 6 10's places
        return self._read_mem_range(0x07de, 6)

    @property
    def _time(self):
        """Return the time left (0 to 999)."""
        # time is represented as a figure with 3 10's places
        return self._read_mem_range(0x07f8, 3)

    @property
    def _coins(self):
        """Return the number of coins collected (0 to 99)."""
        # coins are represented as a figure with 2 10's places
        return self._read_mem_range(0x07ed, 2)

    @property
    def _life(self):
        """Return the number of remaining lives."""
        return self.ram[0x075a]

    @property
    def _x_position(self):
        """Return the current horizontal position."""
        # add the current page 0x6d to the current x
        return self.ram[0x6d]*0x100 + self.ram[0x86]

    @property
    def _left_x_position(self):
        """Return the number of pixels from the left of the screen."""
        # subtract the left x position 0x071c from the current x 0x86
        return (self.ram[0x86] - self.ram[0x071c]) % 256

    @property
    def _y_pixel(self):
        """Return the current vertical position."""
        return self.ram[0x03b8]

    @property
    def _y_viewport(self):
        """
        Return the current y viewport.

        Note:
            1 = in visible viewport
            0 = above viewport
            > 1 below viewport (i.e. dead, falling down a hole)
            up to 5 indicates falling into a hole

        """
        return self.ram[0x00b5]

    @property
    def _y_position(self):
        """Return the current vertical position."""
        # check if Mario is above the viewport (the score board area)
        if self._y_viewport < 1:
            # y position overflows so we start from 255 and add the offset
            return 255 + (255 - self._y_pixel)
        # invert the y pixel into the distance from the bottom of the screen
        return 255 - self._y_pixel

    @property
    def _player_status(self):
        """Return the player status as a string."""
        return self.ram[0x0756]

    @property
    def _player_state(self):
        """
        Return the current player state.

        Note:
            0x00 : Leftmost of screen
            0x01 : Climbing vine
            0x02 : Entering reversed-L pipe
            0x03 : Going down a pipe
            0x04 : Auto-walk
            0x05 : Auto-walk
            0x06 : Dead
            0x07 : Entering area
            0x08 : Normal
            0x09 : Cannot move
            0x0B : Dying
            0x0C : Palette cycling, can't move

        """
        return self.ram[0x000e]

    @property
    def _is_dying(self):
        """Return True if Mario is in dying animation, False otherwise."""
        return self._player_state == 0x0b or self._y_viewport > 1

    @property
    def _is_dead(self):
        """Return True if Mario is dead, False otherwise."""
        return self._player_state == 0x06

    @property
    def _is_game_over(self):
        """Return True if the game has ended, False otherwise."""
        # the life counter will get set to 255 (0xff) when there are no lives
        # left. It goes 2, 1, 0 for the 3 lives of the game
        return self._life == 0xff

    @property
    def _is_busy(self):
        """Return boolean whether Mario is busy with in-game garbage."""
        return self._player_state in _BUSY_STATES

    @property
    def _is_world_over(self):
        """Return a boolean determining if the world is over."""
        # 0x0770 contains GamePlay mode:
        # 0 => Demo
        # 1 => Standard
        # 2 => End of world
        return self.ram[0x0770] == 2

    @property
    def _is_stage_over(self):
        """Return a boolean determining if the level is over."""
        # iterate over the memory addresses that hold enemy types
        for address in _ENEMY_TYPE_ADDRESSES:
            # check if the byte is either Bowser (0x2D) or a flag (0x31)
            # this is to prevent returning true when Mario is using a vine
            # which will set the byte at 0x001D to 3
            if self.ram[address] in _STAGE_OVER_ENEMIES:
                # player float state set to 3 when sliding down flag pole
                return self.ram[0x001D] == 3

        return False

    @property
    def _flag_get(self):
        """Return a boolean determining if the agent reached a flag."""
        return self._is_world_over or self._is_stage_over

    # MARK: RAM Hacks

    def _write_stage(self):
        """Write the stage data to RAM to overwrite loading the next stage."""
        self.ram[0x075f] = self._target_world - 1
        self.ram[0x075c] = self._target_stage - 1
        self.ram[0x0760] = self._target_area - 1

    def _runout_prelevel_timer(self):
        """Force the pre-level timer to 0 to skip frames during a death."""
        self.ram[0x07A0] = 0

    def _skip_change_area(self):
        """Skip change area animations by by running down timers."""
        change_area_timer = self.ram[0x06DE]
        if change_area_timer > 1 and change_area_timer < 255:
            self.ram[0x06DE] = 1

    def _skip_occupied_states(self):
        """Skip occupied states by running out a timer and skipping frames."""
        while self._is_busy or self._is_world_over:
            self._runout_prelevel_timer()
            self._frame_advance(0)

    def _skip_start_screen(self):
        """Press and release start to skip the start screen."""
        # press and release the start button
        self._frame_advance(8)
        self._frame_advance(0)
        # Press start until the game starts
        while self._time == 0:
            # press and release the start button
            self._frame_advance(8)
            # if we're in the single stage, environment, write the stage data
            if self.is_single_stage_env:
                self._write_stage()
            self._frame_advance(0)
            # run-out the prelevel timer to skip the animation
            self._runout_prelevel_timer()
        # set the last time to now
        self._time_last = self._time
        # after the start screen idle to skip some extra frames
        while self._time >= self._time_last:
            self._time_last = self._time
            self._frame_advance(8)
            self._frame_advance(0)

    def _skip_end_of_world(self):
        """Skip the cutscene that plays at the end of a world."""
        if self._is_world_over:
            # get the current game time to reference
            time = self._time
            # loop until the time is different
            while self._time == time:
                # frame advance with NOP
                self._frame_advance(0)

    def _kill_mario(self):
        """Skip a death animation by forcing Mario to death."""
        # force Mario's state to dead
        self.ram[0x000e] = 0x06
        # step forward one frame
        self._frame_advance(0)

    # MARK: Reward Function

    @property
    def _x_reward(self):
        """Return the reward based on left right movement between steps."""
        _reward = self._x_position - self._x_position_last
        self._x_velocity = _reward;
        
        self._x_position_last = self._x_position
        # TODO: check whether this is still necessary
        # resolve an issue where after death the x position resets. The x delta
        # is typically has at most magnitude of 3, 5 is a safe bound
        if _reward < -5 or _reward > 5:
            return 0

        return _reward

    @property
    def _time_penalty(self):
        """Return the reward for the in-game clock ticking."""
        _reward = self._time - self._time_last
        self._time_last = self._time
        # time can only decrease, a positive reward results from a reset and
        # should default to 0 reward
        if _reward > 0:
            return 0

        return _reward

    @property
    def _death_penalty(self):
        """Return the reward earned by dying."""
        if self._is_dying or self._is_dead:
            return -25
        return 0

    @property
    def _enemy_x_positions(self):
        """Return the global x positions of all enemies on screen"""
        return [self.ram[_ENEMY_X_ADDRESSES[i]] + self.ram[_SCREEN_PAGE_SHIFT]*0x100 for i in range(5)];

    @property
    def _enemy_y_positions(self):
        return [(255-self.ram[_ENEMY_Y_ADDRESSES_2[i]]) + (255 if self.ram[_ENEMY_Y_ADDRESSES_1[i]] < 1 else 0) for i in range(5)];

    @property
    def _powerup_position(self):
        return [self.ram[_POWERUP_X_ADDRESS] + self.ram[_SCREEN_PAGE_SHIFT]*0x100,
                (255-self.ram[_POWERUP_Y_ADDRESS_2]) + (255 if self.ram[_POWERUP_Y_ADDRESS_1] < 1 else 0)];

    @property
    def _enemy_types(self):
        return [self.ram[_ENEMY_TYPE_ADDRESSES[i]] for i in range(5)];

    @property
    def _stillness_frames(self):
        if (self._last_level != self._level or self._last_area != self._area or self._last_stage != self._area):
            self._max_x = 0;

        self._last_level = self._level;
        self._last_area = self._area;
        self._last_stage = self._stage;
        
        if (self._max_x >= self._x_position):
            self._stillness_frame_count += 1;
        else:
            self._max_x = self._x_position;
            self._stillness_frame_count = 0;
        #print('stillness: {0}'.format(self._stillness_frame_count));
        #print('current x: {0}'.format(self._x_position));
        #print('max x: {0}'.format(self._max_x));
        
        return self._stillness_frame_count;

    @property
    def _enemy_array(self):
        xs = self._enemy_x_positions;
        ys = self._enemy_y_positions;
        types = self._enemy_types;
        existences = [self.ram[0x000F + i] for i in range(5)];
        selfXPos = self._x_position;
        selfYPos = self._y_position;
        #print('x positions: {0}, y positions: {1}, types: {2}, existences: {3}, my x: {4}, my y: {5}'.format(xs,ys,types,existences,selfXPos,selfYPos));
        result = [[0 for i in range(8)] for j in range(8)];
        for i in range(5):
            if (existences[i]):
                relXBlock = int(round(((xs[i]-selfXPos)/16))+2);
                relYBlock = int(round(((ys[i]-selfYPos)/16))+2);
                #print(str((relXBlock,relYBlock)));
                if (relXBlock in range(8) and relYBlock in range(8)):
                    result[relYBlock][relXBlock] = types[i];
        #print('enemies:');
        #[print(result[7-i]) for i in range(8)];
        return result;
        
    
    @property
    def _blocks_array(self):
        evenArray = ([[self.ram[16*i+j+0x0500] for j in range(16)] for i in range (13)]);
        oddArray = ([[self.ram[16*i+j+0x05D0] for j in range(16)] for i in range (13)]);
        parody = math.floor(self._x_position/256)%2;
        #print('parody: ',parody);
        centerArray = oddArray if parody else evenArray;
        sideArray = evenArray if parody else oddArray;
        wideScreen = [sideArray[i] + centerArray[i] + sideArray[i] for i in range(13)];
        #[print(wideScreen[i]) for i in range(len(wideScreen))];
        leftIndex = math.floor(self._x_position/16)%16+16-3;
        rightIndex = math.floor(self._x_position/16)%16+16+5;
        bottomIndex = math.floor(self._y_position/16)-3;
        #print(bottomIndex);
        #print('left index: ',leftIndex);
        #print('right index: ',rightIndex);
        relevantSquare = [([wideScreen[i][j] for j in range(leftIndex,rightIndex)] if (0 <= i and i < 13) else [0 for j in range(8)] ) for i in range(13-bottomIndex,5-bottomIndex,-1)];
        #print(len(relevantSquare));
        #print(sum([len(relevantSquare[i]) for i in range(len(relevantSquare))]));
        #[print(relevantSquare[i]) for i in range(8)];
        #print('blocks:');
        #[print(relevantSquare[7-i]) for i in range(8)]
        return relevantSquare;

##    @property
##    def _output_array_sizes(self):
##        return (8,8);

    # MARK: nes-py API calls

    def _will_reset(self):
        """Handle and RAM hacking before a reset occurs."""
        self._time_last = 0
        self._x_position_last = 0
        self._stillness_frame_count = 0;
        self._max_x = 0;
        self._last_area = 0;
        self._last_stage = 0;
        self._last_level = 0;

    def _did_reset(self):
        """Handle any RAM hacking after a reset occurs."""
        self._time_last = self._time
        self._x_position_last = self._x_position
        self._stillness_frame_count = 0;
        self._max_x = 0;
        self._last_area = 0;
        self._last_stage = 0;
        self._last_level = 0;

    def _did_step(self, done):
        """
        Handle any RAM hacking after a step occurs.

        Args:
            done: whether the done flag is set to true

        Returns:
            None

        """
        # if done flag is set a reset is incoming anyway, ignore any hacking
        if done:
            return
        # if mario is dying, then cut to the chase and kill hi,
        if self._is_dying:
            self._kill_mario()
        # skip world change scenes (must call before other skip methods)
        if not self.is_single_stage_env:
            self._skip_end_of_world()
        # skip area change (i.e. enter pipe, flag get, etc.)
        self._skip_change_area()
        # skip occupied states like the black screen between lives that shows
        # how many lives the player has left
        self._skip_occupied_states()


    def _get_reward(self):
        """Return the reward after a step occurs."""
        return self._x_reward + self._time_penalty + self._death_penalty

    def _get_done(self):
        """Return True if the episode is over, False otherwise."""
        if self.is_single_stage_env:
            return self._is_dying or self._is_dead or self._flag_get
        return self._is_game_over

    def _get_info(self):
        """Return the info after a step occurs"""
        return dict(
            coins=self._coins,
            flag_get=self._flag_get,
            life=self._life,
            score=self._score,
            stage=self._stage,
            status=self._player_status,
            time=self._time,
            world=self._world,
            x_pos=self._x_position,
            y_pos=self._y_position,
            enemy_type=self._enemy_types,
            enemy_x=self._enemy_x_positions,
            enemy_y=self._enemy_y_positions,
            powerup_x=self._powerup_position[0],
            powerup_y=self._powerup_position[1],
            stillness_time=self._stillness_frames,
            blocks=self._blocks_array,
            enemies=self._enemy_array
        )


# explicitly define the outward facing API of this module
__all__ = [SuperMarioBrosEnv.__name__]
