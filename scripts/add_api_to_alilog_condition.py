import re
import os


def get_query_is(file_path):
    """
    :param file_path: 一个带有api接口的文件路径
    :return: 返回一个tuple的列表 [(query_condition, condition_name),...]
    query_condition是阿里云日志服务相应的查询条件，即query字符串，condition_name是该str变量名字，按照接口路径和请求方式命名：
    eg. ('request_uri:/api/sns/v1/lit/user/avatars AND request_method:GET', ALILOG_USER_AVATARS)
        ('request_uri:/api/sns/v1/lit/user/info AND request_method:POST',ALILOG_USER_INFO_P)
    """
    res = []
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
            if line.strip()[0] == '#':
                continue
            head = re.match(valid_head_pattern, line)
            if head:
                end_head_pos = head.span()[1]
                post_tag = False
                if re.search(post_pattern, line):
                    post_tag = True
                line = line[end_head_pos:]
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
                res_tuple = (condition, name)
                res.append(res_tuple)

    return res


def run(path_set=None):
    """
    :param path_set: 一个文件名的列表，文件中包含api接口描述，eg.['/litatom/api/v1/__init__.py',...]
    :return: 返回值同get_query_is，实际上将其结果整合
    """

    res = []
    for path in path_set:
        file_path = os.getcwd() + path
        res += get_query_is(file_path)
    return res
