from litatom.service import AliLogService


def run():
    AliLogService.put_logs([('user_id', '5e18529f3fff2253c8410e9e'), ('action', 'create_new_user')],
                           logstore='shareaction')
    AliLogService.put_logs([('clicker', '10.244.141.151'), ('action', 'click_share')], logstore='shareaction')


if __name__ == '__main__':
    run()
