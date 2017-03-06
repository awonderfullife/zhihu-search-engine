#!/usr/bin/env python
import sys

def main():
	res = {}
	for x in sys.stdin.readlines():
		sr = x.split()
		if len(sr) > 0:
			if sr[0] not in res.keys():
				res[sr[0]] = [0.0, []]
			res[sr[0]][0] += float(sr[1])
			res[sr[0]][1] += sr[2:]
	for k, v in res.items():
		sys.stdout.write('{0} {1}\t{2}\n'.format(k, v[0], ' '.join(v[1])))

if __name__ == '__main__':
	main()
