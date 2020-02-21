import re
import os


def run():
    res = []
    file_path = os.getcwd() + '/litatom/api/v1/__init__.py'
    with open(file_path) as f:
        lines = f.readlines()
        valid_head_pattern = 'b.add_url_rule\(\'/lit/'
        valid_body_pattern = '[a-z0-9_]+[/\']'
        post_pattern = 'POST'
        name_head = 'ALILOG'
        condition_head = 'request_uri:/api/sns/v1/lit'
        condition_tail_get = ' AND request_method:GET'
        condition_tail_post = ' AND request_method:POST'
        for line in lines:
            # print(line)
            if line.strip()[0] == '#':
                continue
            head = re.match(valid_head_pattern, line)
            if head:
                end_head_pos = head.span()[1]
                post_tag = False
                if re.search(post_pattern, line):
                    post_tag = True
                line = line[end_head_pos:]
                # print(line)
                body = []
                while True:
                    body_part = re.match(valid_body_pattern, line)
                    if not body_part:
                        break
                    end_part_pos = body_part.span()[1]
                    body.append(line[:end_part_pos - 1])
                    line = line[end_part_pos:]
                name = name_head
                condition = condition_head
                for part in body:
                    name += '_'
                    condition += '/'
                    condition += part
                    name += part.upper()
                if post_tag:
                    name += '_P'
                    condition += condition_tail_post
                else:
                    condition += condition_tail_get
                res_line = name + " = '" + condition + "'\n"
                res.append(res_line)
                print(res_line)
        f.close()

    with open('../litatom/api_condition.py', 'w') as f:
        f.writelines(res)
        f.close()


if __name__ == '__main__':
    run()
