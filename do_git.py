#!/usr/bin/env python
# coding: utf-8

# In[1]:


try:
    from git import Git
except:
    #安装模块GitPython
    import os
    try:
        exitcode = os.system('pip install GitPython')
        if exitcode != 0:
            os._exit(0)
    except:
        os._exit(0)
from git import Git

try:
    from dateutil.parser import parse
except:
    #安装模块GitPython
    import os
    try:
        exitcode = os.system('pip3 install python-dateutil')
        if exitcode != 0:
            os._exit(0)
    except:
        os._exit(0)
from dateutil.parser import parse
msg = 'pycharm'


# In[2]:


r = Git("C:/Users/chenh/PycharmProjects/auto_BBDown/")


# In[3]:


def get_com_dict(r,origin=False):
    if origin:
        r.execute('git fetch', shell=True)
        aa = r.execute('git log origin -3', shell=True)
    else:
        try:
            r.execute('git add .', shell=True)
            r.commit('-m {}'.format(msg))
        except:
            pass
        aa = r.execute('git log -3', shell=True)
    commits = []
    commits_list = []
    where_list = []

    for i in aa.split('\n\n'):
    #     print('='*30)
    #     print(i)
        if 'Date:' in i:
            commits_list.append(i)
        else:
            where_list.append(i)
    # print(len(commits_list))
    # print(len(where_list))
    for i, v in enumerate(commits_list):
    #     print(v)
        a = v.split('\n')
        commit_name = a[0].strip()
        dict = {}
        a.pop(0)
    #     print(a)
        for b in a:
            c = b.split(':',1)
            if c[0].strip() == 'Date':
                date = parse(c[1].strip())
                dict[c[0].strip()] = date
            else:
                dict[c[0].strip()] = c[1].strip()
        dict['info'] = where_list[i].strip()
        commits.append(dict)

#     for i in commits:
#         print('='*30)
#         print(i)
#         print(commits[i])
    return commits


# In[4]:


local = get_com_dict(r)
# local


# In[5]:


github = get_com_dict(r,origin=True)
# github


# In[6]:


github_dt = github[0]['Date']
local_dt = local[0]['Date']


# In[7]:


if github_dt > local_dt:
    print('从github拉取')
    r.execute('git pull', shell=True)
elif github_dt < local_dt:
    print('同步到github')
    r.execute('git push', shell=True)
else:
    print('代码已经同步')
print('完成')


# In[ ]:




