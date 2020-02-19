import re

def run():
    with open('../litatom/api/v1/__init__.py') as f:
        print(f.readlines())


if __name__ == '__main__':
    run()