
import os

script_dir = os.path.dirname(os.path.abspath(__file__))  # Get current script directory
intra_shard_file_path = os.path.join(script_dir, 'test/intra_shard_test_1000.txt')
cross_shard_file_path = os.path.join(script_dir, 'test/cross_shard_test_1000.txt')
intra_cross_shard_file_path = os.path.join(script_dir, 'test/intra_cross_shard_test_500.txt')

def generate_intrashard_input_file():
    # 500 intra-shard transactions
    with open(intra_shard_file_path, 'w') as file:

        for i in range(1, 1000):
            # data item will be like (x,y,amt)
            file.write(f'({i}, {i + 1}, 5)\n')

        file.write(f'(1000, 1, 5)')

def generate_cross_shard_input_file():
    # 500 cross-shard transactions
    with open(cross_shard_file_path, 'w') as file:

        for i in range(1, 501):
            # data item will be like (x,y,amt)
            file.write(f'({i}, {i + 1000}, 3)\n')

        for i in range(1, 501):
            # data item will be like (x,y,amt)
            file.write(f'({i + 1000}, {i}, 3)\n')

def generate_intra_cross_input_file():
    # 500 intra-shard and 500 cross-shard transactions
    with open(intra_cross_shard_file_path, 'w') as file:

        for i in range(1, 1000, 3):
                # data item will be like (x,y,amt)
            file.write(f'({i}, {i + 1}, 1)\n')
            file.write(f'({i + 2}, {i + 1000}, 1)\n')
            # 1, 1001 -> 250, 1250

        # for i in range(500, 0, -3):
        #         # data item will be like (x,y,amt)
        #     file.write(f'({i + 1}, {i}, 1)\n')
        #     file.write(f'({i + 1000}, {i + 2}, 1)\n')

if __name__ == "__main__":

    # generate_intrashard_input_file()

    # generate_cross_shard_input_file()

    generate_intra_cross_input_file()