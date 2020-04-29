# encoding:utf-8
from litatom.service import (
    AliLogService,
)


def read_uids_from_file(path):
    uids = []
    with open(path, mode='r') as f:
        uids = f.readlines()
    return uids


def deal_uids(uids):
    for i in range(len(uids)):
        uids[i] = uids[i][4:-16]
    return uids


def get_active_uids():
    resp_set = AliLogService.get_log_by_time_and_topic(from_time='2020-04-29 00:00:00+8:00',
                                                       to_time='2020-04-30 00:00:00+8:00',
                                                       query='*|select distinct user_id limit 500000')
    uids = set()
    for resp in resp_set:
        for log in resp.logs:
            content = log.get_contents()
            user_id = content['user_id']
            uids.add(user_id)
    return uids


def load_uid_payment(default_uids, exp_uids):
    resp = AliLogService.get_log_atom(project='litatom-account', logstore='account_flow',
                                      from_time='2020-04-28 00:00:00+8:00',
                                      to_time='2020-04-30 00:00:00+8:00',
                                      query="name:deposit | SELECT user_id,sum(diamonds) as res GROUP by user_id limit 500000")
    default_pay_sum = 0
    exp_pay_sum = 0
    default_pay_num = set()
    exp_pay_num = set()
    for log in resp.logs:
        content = log.get_contents()
        user_id = content['user_id']
        res = content['res']
        if user_id in default_uids:
            default_pay_sum += int(res)
            default_pay_num.add(user_id)
        elif user_id in exp_uids:
            exp_pay_sum += int(res)
            exp_pay_num.add(user_id)

    return default_pay_sum, exp_pay_sum, len(default_pay_num), len(exp_pay_num)


def run():
    exp_uids = read_uids_from_file('/data/exp/4-28/exp_ids')
    exp_uids = deal_uids(exp_uids)
    len_exp_uids = float(len(exp_uids))
    print(len_exp_uids)
    default_uids = read_uids_from_file('/data/exp/4-28/default_ids')
    default_uids = deal_uids(default_uids)
    len_default_uids = float(len(default_uids))
    print(len_default_uids)

    default_pay_sum, exp_pay_sum, default_pay_num, exp_pay_num = load_uid_payment(default_uids, exp_uids)

    print('对照组付费平均值:', default_pay_sum / len_default_uids, '对照组付费用户比例:', default_pay_num / len_default_uids)
    print('实验组付费平均值:', exp_pay_sum / len_exp_uids, '实验组付费用户比例', exp_pay_num / len_exp_uids)

    active_uids = get_active_uids()

    print('对照组留存比例', len(active_uids & set(default_uids)) / len_default_uids)
    print('实验组留存比例', len(active_uids & set(exp_uids)) / len_exp_uids)


if __name__ == '__main__':
    run()
