import  os

def down():
    f = open('tt').read().split('\n')
    urls = []
    for el in f:
        if 'data' not in el:
            continue
        url = el.split('data\\":\\"')[1].split('\\"}"')[0]
        urls.append(url)
        print url
    cnt = 0
    save_dir = '/data/musics/turkey_army/'
    for _ in urls:
        cnt += 1
        cmd = "wget \'%s\' -O %s" % (_, save_dir + str(cnt) + '.mp3')
        print cmd
        os.system(cmd)

# rs = ToDevSyncService.sync(RegionWord, '2020-05-10')


if __name__ == '__main__':
    down()