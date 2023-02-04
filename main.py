import matplotlib.pyplot as plt
import csv

time_min_arr: list[float] = []
temp1_arr: list[int] = []
temp2_arr: list[int] = []
with open('main.csv', 'r') as csvfile:
    plots = csv.reader(csvfile, delimiter=',')
    for row in plots:
        if len(row) == 3:
            # print(len(row))
            try:
                time_sec: float = int(row[2])
                temp1: int = int(row[0])
                temp2: int = int(row[1])
                time_min_arr.append(time_sec / 60)
                temp1_arr.append(temp1)
                temp2_arr.append(temp2)
            except:
                print('NaN ' + row[0] + ' ' + row[1])

plt.grid()
plt.scatter(time_min_arr, temp1_arr, s=3)
plt.scatter(time_min_arr, temp2_arr, s=3)
plt.xlabel('Time')
plt.ylabel('Temperature')
plt.show()

