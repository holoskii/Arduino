import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import sys

def process_numbers(line):
    parts = line.strip().split(',')
    numbers = []
    for part in parts:
        # Check if the current part is a number
        if part.isdigit():
            numbers.append(int(part))
        else:
            # If the current part is not a number, check if it starts with a number
            num_str = ""
            for char in part:
                if char.isdigit():
                    num_str += char
                else:
                    break
            if num_str:
                numbers.append(int(num_str))
                break
    return numbers

def read_file_and_process_data(file_path):
    time_values: list[float] = []
    temp1_values: list[int] = []
    temp2_values: list[int] = []
    with open(file_path, 'r') as file:
        for line in file:
            if len(line) <= 1:
                continue

            values = line.split(' ', 1);
            if len(values) != 2:
                print('Line without data (not 2 values): ' + str(line))
                continue
            first_part, rest_of_line = values[0], values[1]
            if first_part != 'D':
                print('Line without data(Not \'D\'): ' + str(line))
                continue

            numbers = process_numbers(rest_of_line)
            if numbers and len(numbers) != 3:
                print('Unexpected number count(' + str(len(numebrs)) + '): ' + str(line))
                continue

            time_values.append(numbers[2] / 60)
            temp1_values.append(numbers[0])
            temp2_values.append(numbers[1])
    return time_values, temp1_values, temp2_values

def animate(i):
    time_values, temp1_values, temp2_values = read_file_and_process_data('output.file')
    plt.clf();
    plt.grid()
    plt.xlabel('Time, min')
    plt.ylabel('Temperature, C')
    plt.scatter(time_values, temp1_values, label='1', s=5)
    plt.scatter(time_values, temp2_values, label='2', s=5)

def main():
    fig = plt.figure()
    ani = animation.FuncAnimation(fig, animate, interval=5000)
    plt.show()

if __name__ == "__main__":
    print('cmd entry:', sys.argv)
    if len(sys.argv) >= 2:
        print('Overriding file path to: ' + sys.argv[1])
        file_path = sys.argv[1]
    main()