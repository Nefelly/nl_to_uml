import os


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

def g(u):
     r = HuanxinService.get_user(u)
     return r.get('notifier_name', '')

huanxin_ids = [el.huanxin.user_id for el in User.objects().order_by('-create_time').limit(10000)]

for _ in huanxin_ids:
    r[_] = g(_)
# rs = ToDevSyncService.sync(RegionWord, '2020-05-10')


if __name__ == '__main__':
    down()