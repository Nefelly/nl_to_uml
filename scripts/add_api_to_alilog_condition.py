import re


def run():
    with open('/litatom/api/v1/__init__.py', encoding='utf-8') as f:
        lines = f.readlines()
        valid_head_pattern = 'b.add_url_rule(\'/lit/'
        valid_body_pattern = '[a-z0-9_]+/'
        for line in lines:
            head = re.match(valid_head_pattern, line)
            if head:
                end_head_pos = head.span()[1]
                line = line[end_head_pos:]
                body = []
                while True:
                    body_part = re.match(valid_body_pattern, line)
                    if not body_part:
                        break
                    end_part_pos = body_part.span()[1]
                    body.append(line[:end_part_pos])
                    line = line[end_part_pos:]
                print(body)


if __name__ == '__main__':
    run()
