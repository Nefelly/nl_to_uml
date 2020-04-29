# encoding:utf-8


def read_uids_from_file(path):
    uids = []
    with open(path, mode='r') as f:
        uids = f.readlines()
    return uids


def deal_uids(uids):
    for i in range(len(uids)):
        uids[i] = uids[i][4:-16]
    return uids

def accum_pay_number(uids):
    cnt = 0
    for uid in uids:
        pass

def run():
    exp_uids = read_uids_from_file('exp_ids')
    exp_uids = deal_uids(exp_uids)
    default_uids = read_uids_from_file('default_ids')
    default_uids = deal_uids(default_uids)

    exp_pay_nums = accum_pay_number(exp_uids)
    default_pay_nums = accum_pay_number(default_uids)




if __name__ == '__main__':
    run()
