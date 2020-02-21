from litatom.service import AliLogService


def run():
    res_set = AliLogService.get_log_by_time_and_topic(project='litatom', size=100, logstore='litatomstore')
    sum = 0.0
    for res in res_set:
        res.log_print()
        for logs in res.logs:
            contents = logs.get_contents()
            sum += contents['upstream_response_time']
    print(sum)


if __name__ == '__main__':
    run()
