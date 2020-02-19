from litatom.service import AliLogService


def run():
    res_set = AliLogService.get_log_by_time_and_topic(query="request_uri\:/api/sns/v1/lit/user AND "
                                                            "request_method\:GET|SELECT regexp_extract(request_uri, "
                                                            "'\^\[0-9a-f\]\{24\}'),upstream_response_time", size=100)
    for res in res_set:
        res.log_print()


if __name__ == '__main__':
    run()
