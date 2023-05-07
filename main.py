import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys
import time

file_path = 'out.txt'

def read_file():
    time_values:     list[float] = []
    temp1_values:    list[float] = []
    control1_values: list[float] = []
    temp2_values:    list[float] = []
    control2_values: list[float] = []

    with open(file_path, 'r') as file:
        for line in file:
            # Check that the line looks valid
            if len(line) <= 1 or not line.startswith("INFO"):
                continue

            # Verify that the line contains data
            delimiter_index = line.find(' ')
            if delimiter_index == -1:
                print(f"Line without data (no space): {line}")
                continue

            # Extract numbers from the line
            numbers: list[float] = []
            for part in line[delimiter_index + 1:].split(','):
                numbers.append(float(part))

            # Verify again
            if len(numbers) != 5:
                print(f"Unexpected number count ({len(numbers)}): {line}")
                continue

            # Assign data to corresponding lists
            time_values.append(numbers[0] / 60)
            temp1_values.append(numbers[1])
            control1_values.append(numbers[2])
            temp2_values.append(numbers[3])
            control2_values.append(numbers[4])
    
    # Build title
    temp1 = temp1_values[-1] if len(temp1_values) > 0 else 0
    temp2 = temp2_values[-1] if len(temp2_values) > 0 else 0
    temps_str = "Substrate B: {:3.01f}°C, Source R: {:3.01f}°C".format(temp1, temp2);
    title = f'{temps_str}'
    return time_values, temp1_values, control1_values, temp2_values, control2_values, title

def update_graph(frame):
    start = time.time()

    time_values, temp1_values, control1_values, temp2_values, control2_values, title = read_file()

    end = time.time()
    print("File parsing time = {:.0f} ms".format(1000 * (end - start)))
    plt.clf()
    plt.grid()
    plt.title(title, fontsize = 20, y=1.04)
    plt.xlabel('Time, min', fontsize=20)
    plt.ylabel('Temperature, C', fontsize=20)
    plt.scatter(time_values, temp1_values, label='Substrate', s=3, color = 'b')
    plt.scatter(time_values, control1_values, s=3, color = 'b')
    plt.scatter(time_values, temp2_values, label='Source', s=3, color = 'r')
    plt.scatter(time_values, control2_values, s=3, color = 'r')
    plt.legend()


def main():
    fig = plt.figure()
    ani = animation.FuncAnimation(fig, update_graph, interval=500)
    plt.show()

if __name__ == "__main__":
    print(f"cmd entry: {sys.argv}")
    if len(sys.argv) >= 2:
        print(f"Overriding file path to: {sys.argv[1]}")
        file_path = sys.argv[1]
    main()
