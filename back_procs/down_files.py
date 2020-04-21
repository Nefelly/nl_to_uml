import  os

def down():
    f = open('tt').read().split('\n')
    urls = [el.split('data\\":\\"')[1].split('\\"}"')[0] for el in f if el]
    cnt = 0
    save_dir = 'data/musics/'
    for _ in urls:
        cnt += 1
        cmd = "wget \'%s\' -O %s" % (_, save_dir + str(cnt) + '.mp4')
        print cmd
        os.system(cmd)


if __name__ == '__main__':
    down()