from litatom.service import AliLogService


def run():
    res_set = AliLogService.get_log_atom(project='litatom', logstore='litatomstore',
                                         query='request_uri:/api/sns/v1/lit/user/info AND request_method:POST'
                                                '|SELECT avg(upstream_response_time) as avg_resp_time,'
                                                'count(1) as called_num,avg(status) as avg_status',
                                         from_time='2020-02-23 20:30:00+8:00',
                                         to_time='2020-02-23 20:31:00+8:00')
    for log in res_set.logs:
        log.log_print()
        contents=log.get_contents()
        print(contents['avg_resp_time'])
        print(contents['called_num'])
        print(contents['avg_status'])


if __name__ == '__main__':
    run()
