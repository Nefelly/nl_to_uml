from litatom.service import AliLogService


def run():
    res_set = AliLogService.get_log_by_time_and_topic(project='litatom', size=-1, logstore='litatomstore',
                                                      query='request_uri:/api/sns/v1/lit/user/info AND request_method:POST'
                                                            '|SELECT avg(upstream_response_time) as avg_resp_time,'
                                                            'count(1) as called_num,avg(status) as avg_status',
                                                      from_time='2020-02-23 20:30:00+8:00',
                                                      to_time='2020-02-23 20:31:00+8:00')
    for res in res_set:
        res.log_print()


if __name__ == '__main__':
    run()
