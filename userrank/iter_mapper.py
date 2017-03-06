#!/usr/bin/env python
import sys, mr_common

def main():
	res = {}
	i = 0
	for x in sys.stdin.readlines():
		sr = x.split()
		if len(sr) > 0:
			if sr[0] not in res.keys():
				res[sr[0]] = [0.0, '']
			res[sr[0]][0] += (1.0 - mr_common.ALPHA) * mr_common.INITIAL_VALUE
			if len(sr) > 2:
				res[sr[0]][1] = ' '.join(sr[2:])
				cv = float(sr[1]) / (len(sr) - 2)
				for y in sr[2:]:
					if y not in res.keys():
						res[y] = [0.0, '']
					res[y][0] += mr_common.ALPHA * cv
	for k, v in res.items():
		sys.stdout.write('{0} {1}\t{2}\n'.format(k, v[0], v[1]))

if __name__ == '__main__':
	main()
