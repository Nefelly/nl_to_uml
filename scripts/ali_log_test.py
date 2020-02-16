from litatom.service import AliLogService
from time import time
from datetime import *


def run():
    start_time = "2020-02-15 00:00:00+8:00"
    end_time = "2020-02-15 00:59:59+8:00"
    for i in range(24):
        hour = int(start_time[11:13]) + i
        if hour < 10:
            str_hour = '0' + str(hour)
        else:
            str_hour = str(hour)
        start = start_time[0:11] + str_hour + start_time[13:]
        end = end_time[0:11] + str_hour + end_time[13:]
        start_match_logs = AliLogService.get_log_by_time(
            query='remark:startMatch and action:match', size=20, from_time=start,
            to_time=end)
        for start_match_log in start_match_logs.logs:
            contents = start_match_log.get_contents()
            user_id = contents['user_id']
            session_id = contents['session_id']
            start_match_time = start_match_log.get_time()
            match_success_text_logs = AliLogService.get_log_by_time(from_time=start_match_time, to_time=start_match_time + 180,
                                                                    query='remark:matchSuccesstext and '
                                                                          'action:match and user_id:' + user_id +
                                                                          ' and session_id:' + session_id).logs
            match_success_voice_logs = AliLogService.get_log_by_time(from_time=start_match_time, to_time=start_match_time + 180,
                                                                     query='remark:matchSuccessvoice and '
                                                                           'action:match and user_id:' + user_id +
                                                                           ' and session_id:' + session_id).logs
            match_success_video_logs = AliLogService.get_log_by_time(from_time=start_match_time, to_time=start_match_time + 180,
                                                                     query='remark:matchSuccessvideo and '
                                                                           'action:match and user_id:' + user_id +
                                                                           ' and session_id:' + session_id).logs
            match_success_logs = []
            if match_success_voice_logs:
                match_success_logs = match_success_voice_logs
                contents['matchType'] = 'voice'
            elif match_success_video_logs:
                match_success_logs = match_success_video_logs
                contents['matchType'] = 'video'
            elif match_success_text_logs:
                match_success_logs = match_success_text_logs
                contents['matchType'] = 'text'
            if match_success_logs:
                min_time = match_success_logs[0].get_time()
                if len(match_success_logs) > 1:
                    for log in match_success_logs:
                        tmp_time = log.get_time()
                        if tmp_time < min_time:
                            min_time = tmp_time
                contents['matchTime'] = min_time - start_match_time
            else:
                continue
        start_match_logs.log_print()

    # for log_set in start_match_logs:
    #     for start_match_log in log_set.logs:
    #         contents = start_match_log.get_contents()
    #         user_id = contents['user_id']
    #         session_id = contents['session_id']
    #         time = start_match_log.get_time()
    #             leave_logs = []
    #             if contents['matchType'] == 'voice' or contents['matchType'] == 'video':
    #                 leave_logs = AliLogService.get_log_by_time_and_topic(from_time=min_time, to_time=min_time + 420,
    #                                                                      query='remark:leave and '
    #                                                                            'action:match and user_id:' + user_id +
    #                                                                            ' and session_id:' + session_id).logs
    #             elif contents['matchType'] == 'text':
    #                 leave_logs = AliLogService.get_log_by_time_and_topic(from_time=min_time, to_time=min_time + 180,
    #                                                                      query='remark:leave and '
    #                                                                            'action:match and user_id:' + user_id +
    #                                                                            ' and session_id:' + session_id).logs
    #             if leave_logs:
    #                 leave_min_time = leave_logs[0].get_time()
    #                 for log in leave_logs:
    #                     tmp_time = log.get_time()
    #                     if tmp_time < leave_min_time:
    #                         leave_min_time = tmp_time
    #                 contents['chatTime'] = leave_min_time - min_time
    #             else:
    #                 contents['chatTime'] = 180
    #         else:
    #             contents['matchTime'] = 180
    #             contents['chatTime'] = 0
    #     log_set.log_print()


if __name__ == "__main__":
    run()
