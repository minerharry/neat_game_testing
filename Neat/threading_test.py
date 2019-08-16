import concurrent.futures

def do_a_thing(num):
    print('thing: ' + str(pow(num,100)));
    print();
    return;

executor = concurrent.futures.ThreadPoolExecutor();
futures = [executor.submit(do_a_thing,num) for num in range(0,100)];
concurrent.futures.wait(futures);

