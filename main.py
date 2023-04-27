import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys

file_path = 'out.txt'

def process_line(line):
    parts = line.strip().split(',')
    numbers = []
    for part in parts:
        numbers.append(float(part))
    return numbers

def read_file():
    time_values = []
    temp1_values = []
    control1_values = []

    temp2_values = []
    control2_values = []
    last_time: int = 0
    with open(file_path, 'r') as file:
        for line in file:
            if len(line) <= 1:
                continue
            values = line.split(' ', 1)
            if len(values) != 2:
                print(f"Line without data (not 2 values): {line}")
                continue
            first_part, rest_of_line = values[0], values[1]
            if first_part != 'INFO:':
                if first_part != 'TRACE:':
                    print(f"Line without data (not 'LINE:'): {line}")
                continue
            numbers = process_line(rest_of_line)
            if numbers and len(numbers) != 5:
                print(f"Unexpected number count ({len(numbers)}): {line}")
                continue
            last_time = numbers[0]
            time_values.append(numbers[0])
            temp1_values.append(numbers[1])
            control1_values.append(numbers[2])
            temp2_values.append(numbers[3])
            control2_values.append(numbers[4])
    # time_str = "{:02d}:{:02d}".format(int(int(last_time) / 60), int(last_time) % 60)
    temps_str = "Substrate: {:3.02f}°C, Source: {:3.02f}°C".format(temp1_values[-1], temp2_values[-1]);
    title = f'{temps_str}'
    return time_values, temp1_values, control1_values, temp2_values, control2_values, title

def update_graph(frame):
    time_values, temp1_values, control1_values, temp2_values, control2_values, title = read_file()
    plt.clf()
    plt.grid()
    plt.title(title, fontsize = 20)
    plt.xlabel('Time, min')
    plt.ylabel('Temperature, C')
    plt.scatter(time_values, temp1_values, label='1', s=3, color = 'c')
    plt.scatter(time_values, control1_values, label='2', s=3, color = 'g')
    plt.scatter(time_values, temp2_values, label='3', s=3, color = 'm')
    plt.scatter(time_values, control2_values, label='4', s=3, color = 'r')

def main():
    fig = plt.figure()
    ani = animation.FuncAnimation(fig, update_graph, interval=1000)
    plt.show()

if __name__ == "__main__":
    print(f"cmd entry: {sys.argv}")
    if len(sys.argv) >= 2:
        print(f"Overriding file path to: {sys.argv[1]}")
        file_path = sys.argv[1]
    main()
