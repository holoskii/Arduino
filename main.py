import matplotlib.pyplot as plt
import csv

x = []
y = []
with open('main.csv','r') as csvfile:
	plots = csv.reader(csvfile, delimiter = ',')
	for row in plots:
		if(len(row) == 2):
			# print(len(row))
			x.append(row[1])
			y.append(int(row[0]))

plt.bar(x, y, color = 'g', width = 0.72, label = "Age")
plt.xlabel('Names')
plt.ylabel('Ages')
plt.title('Ages of different persons')
plt.legend()
plt.show()
