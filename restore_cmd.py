# convert a bytes string into a mp3 image back
import sys
dim_1 = sys.argv[1]
dim_2 = sys.argv[2]
dim = '{0}_{1}'.format(dim_1, dim_2)

bytearr = [chr((ord(c)+128)&255) for c in sys.stdin.read()[::2]]

sys.stdout.write('P5\n{0}\n255\n'.format(dim)+''.join(bytearr))
