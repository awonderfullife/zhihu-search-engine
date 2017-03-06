import sys

def main():
	x = set()
	reslines = []
	for line in sys.stdin.readlines():
		y = line.split()
		reslines.append(y)
		x.add(y[0])
	for line in reslines:
		first = True
		sys.stdout.write('{0}\t{1}\t'.format(line[0], line[1]))
		for obj in line[2:]:
			if obj in x:
				if not first:
					sys.stdout.write(' ')
				else:
					first = False
				sys.stdout.write(obj)
		sys.stdout.write('\n')

if __name__ == '__main__':
	main()
