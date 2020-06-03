# encoding:utf-8
from litatom.service import (
    AliLogService,
    ExperimentAnalysisService
)

from litatom.util import (
    parse_standard_time,
    next_date,
    format_standard_date,
    date_from_str
)


def read_uids_from_file(path):
    uids = []
    with open(path, mode='r') as f:
        uids = f.readlines()
    return uids


def deal_uids_pos(uids):
    for i in range(len(uids)):
        uids[i] = uids[i][4:-16]
    return uids


def deal_uids_tail(uids):
    for i in range(len(uids)):
        uids[i] = uids[i][:-1]
    return uids


def get_active_uids(from_date, to_date):
    res = ExperimentAnalysisService.get_active_users_by_date(from_date)
    if res:
        return set(res)
    resp_set = AliLogService.get_log_by_time_and_topic(from_time=AliLogService.datetime_to_alitime(from_date),
                                                       to_time=AliLogService.datetime_to_alitime(to_date),
                                                       query='*|select distinct user_id limit 500000')
    uids = set()
    for resp in resp_set:
        for log in resp.logs:
            content = log.get_contents()
            user_id = content['user_id']
            uids.add(user_id)
    return uids


def load_uid_payment(default_uids, exp_uids, from_time, to_time):
    resp = AliLogService.get_log_atom(project='litatom-account', logstore='account_flow',
                                      from_time=AliLogService.datetime_to_alitime(from_time),
                                      to_time=AliLogService.datetime_to_alitime(to_time),
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


def get_exp_res(default_uids, exp_uids, from_date, to_date):
    len_default_uids = len(default_uids)
    len_exp_uids = len(exp_uids)

    default_pay_sum, exp_pay_sum, default_pay_num, exp_pay_num = load_uid_payment(default_uids, exp_uids, from_date,
                                                                                  to_date)

    print('payment average of default group:', default_pay_sum / len_default_uids,
          'payment user rate average of default group:', default_pay_num / len_default_uids)
    print('payment average of experiment group:', exp_pay_sum / len_exp_uids,
          'payment user rate average of experiment group:', exp_pay_num / len_exp_uids)

    payment_res = [[default_pay_sum / len_default_uids, default_pay_num / len_default_uids],
                   [exp_pay_sum / len_exp_uids, exp_pay_num / len_exp_uids]]

    i = 0

    sum_default_rate = 0.0
    sum_exp_rate = 0.0

    origin_len_default_uids = len_default_uids
    origin_len_exp_uids = len_exp_uids
    default_retain_res = [(from_date, origin_len_default_uids, 1)]
    exp_retain_res = [(to_date, origin_len_exp_uids, 1)]
    origin_from_date = from_date
    while from_date <= next_date(to_date, -1):
        i += 1
        nextdate = next_date(from_date)
        active_uids = get_active_uids(from_date, nextdate)
        default_uids = active_uids & set(default_uids)
        new_len_default_uids = len(default_uids)
        default_retain_rate = new_len_default_uids / len_default_uids
        print(nextdate, 'retain rate of default group: ', new_len_default_uids, '/', len_default_uids, '=',
              default_retain_rate,)
        default_retain_res.append((new_len_default_uids, default_retain_rate))
        len_default_uids = float(new_len_default_uids)

        exp_uids = active_uids & set(exp_uids)
        new_len_exp_uids = len(exp_uids)
        exp_retain_rate = new_len_exp_uids / len_exp_uids
        print(from_date, nextdate, 'retain rate of experiment group: ', new_len_exp_uids, '/', len_exp_uids, '=',
              exp_retain_rate,)
        exp_retain_res.append((new_len_exp_uids, exp_retain_rate))
        len_exp_uids = float(new_len_exp_uids)

        sum_default_rate += default_retain_rate
        sum_exp_rate += exp_retain_rate

        from_date = nextdate

    print('total ', i, 'days')
    print('average retain rate of default group:', sum_default_rate / i)
    print('average retain rate of experiment group:', sum_exp_rate / i)

    write_data('/data/exp', payment_res, [default_retain_res, exp_retain_res], origin_from_date, next_date(to_date, -1))


def write_data(name, payment_data, retain_data, from_date, to_date):
    """

    :param name:
    :param sheet_names:
    :param tb_heads:
    :param data:一个列表，列表中的每个元素也是一个列表，每个元素都是1个sheet中的数据
    :return:
    """
    import xlwt
    f = xlwt.Workbook(encoding='utf-8')
    sheet_names = [u'付费', u'留存']
    # 建表
    sheets = [f.add_sheet(s) for s in sheet_names]
    # 写表头
    payment_sheet = sheet_names[0]
    retain_sheet = sheet_names[1]

    i = 1
    while from_date <= to_date:
        retain_sheet.write(i, 0, format_standard_date(from_date))
        i += 1
        from_date = next_date(from_date, 1)

    payment_sheet.write(0, 1, u'对照组')
    payment_sheet.write(0, 2, u'实验组')
    payment_sheet.write(1, 0, u'人均付费')
    payment_sheet.write(2, 0, u'付费比例')

    for col_num in payment_data:
        col_data = payment_data[col_num]
        for row_num in col_data:
            payment_sheet.write(row_num + 1, col_num + 1, col_data[row_num])

    retain_sheet.write(0, 1, u'对照组')
    retain_sheet.write(0, 2, u'实验组')
    for col_num in retain_data:
        col_data = retain_data[col_num]
        for row_num in col_data:
            retain_sheet.write(row_num + 1, col_num + 1, col_data[row_num])
    f.save(name)


def run():
    # exp_uids = read_uids_from_file('/data/exp/match-428/exp_ids')
    # exp_uids = deal_uids_pos(exp_uids)
    # another_exp_uids = read_uids_from_file('/data/exp/match-428/exp')
    # another_exp_uids = deal_uids_tail(another_exp_uids)
    # print('experiment group: first size', len(exp_uids), 'second size', len(another_exp_uids))
    # exp_uids += another_exp_uids
    # exp_uids = set(exp_uids)
    # len_exp_uids = float(len(exp_uids))
    # print(len_exp_uids)
    #
    # default_uids = read_uids_from_file('/data/exp/match-428/default_ids')
    # default_uids = deal_uids_pos(default_uids)
    # another_default_uids = read_uids_from_file('/data/exp/match-428/default')
    # another_default_uids = deal_uids_tail(another_default_uids)
    # print('default group:first size', len(default_uids), 'second size', len(another_default_uids))
    # default_uids += another_default_uids
    # default_uids = set(default_uids)
    # len_default_uids = float(len(default_uids))
    # print(len_default_uids)
    default_uids, exp_uids = ExperimentAnalysisService.default_exp_values('feed_age_control')
    from_date = date_from_str('2020-05-31')
    to_date = date_from_str('2020-06-02')
    get_exp_res(default_uids, exp_uids, from_date, to_date)


if __name__ == '__main__':
    run()
