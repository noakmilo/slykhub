from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort

from slykhub.auth import login_required
from slykhub.db import get_db
from urllib.error import HTTPError
from .api import(
    get_verified_users , get_enabled_tasks, complete_task, 
    get_wallet_balance, get_users, get_payment_methods,
    get_completed_transactions
)


bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def redir():
    return redirect(url_for('dashboard.home'))

@bp.route('/home')
@login_required
def home():
        return render_template('dashboard/home.html')

@bp.route('/tasks', methods=('GET', 'POST'))
@login_required
def tasks():
    error = None
    if request.method == 'POST':
        selected_task = request.form['task']
        if not selected_task:
            error='No selected task'
        user_ids =request.form.getlist('taskcheckbox')
        if not user_ids:
            error='No selected users'
            
        if not error:
            print(f'User Tasks to complete: {len(user_ids)}')
            error=complete_task(selected_task, user_ids, session['api_key'])
            if error is not HTTPError:
                err422 = error
                succ = len(user_ids)-err422
                error = 'Selected users already completed the task' if succ == 0 else None
        if not error:  
            flash(f'Successfully completed task for {succ} users.', 'success')
            
    headers=('User','Email', 'Select All')
    #headers=('User','Email', 'Balance', 'Select All')
    rows=[]
    tasks=[]
    user_data = get_verified_users(session['api_key'])
    if user_data is HTTPError:
        error = user_data
    else:
        for user in user_data['data']:
            if 'user' in user['roles']:
                (username, email, ids) = (user['name'], user['email'], user['id'])
                ######################### With Balance ################# 
                # wallet = user['primaryWalletId']
                # balancedata = get_wallet_balance(session['api_key'], wallet)
                # if balancedata is HTTPError:
                #     error = balancedata
                # else:  
                #     #balance = balancedata['data']
                #     #rows.append((username, email, balance, ids))
                ######################### Without Balance #################
                rows.append((username, email, ids))
                ######################### END #################
    tasks_data=get_enabled_tasks(session['api_key'])
    if tasks_data is HTTPError:
        error = tasks_data
    else:
        for task in tasks_data['data']:
            tasks.append(task['name'])
                
    if error:
        flash(error, 'error')
    return render_template('dashboard/tasks.html', headers=headers, rows=rows, tasks=tasks)

@bp.route('/sales')
@login_required
def sales():
    error=''
    payment_methods = {}
    pm = get_payment_methods(session['api_key'])
    if pm is HTTPError:
        error = pm
    else:
        for p in pm['data']:
            if p['connected']:
                payment_methods[p['name']] = p['slug']
        print (f'This is the payment methods dictionary: {payment_methods}')
    payment_methods_data =[]
    pdata=[]
    ct = get_completed_transactions(session['api_key'])            
    if ct is Exception:
        print(ct)
        error = ct
    else:
        print(ct)
        dicti = dict.fromkeys(payment_methods.values(), 0)
        for trans in ct['data']:
            if 'internal' not in trans['code']:
                splitted = trans['code'].split(':')
                print(splitted)
                pm_name = splitted[-1]
                if dicti.get(pm_name) is None:
                    pretty_payname = ' '.join(list(map(str.capitalize,splitted)))
                    payment_methods[pretty_payname]=pm_name
                    dicti[pm_name]=0
                dicti[pm_name] = dicti[pm_name] + 1
        
        pdata = list(dicti.values())                       
        payment_methods_data = [{
                        'label': '# Successful payments',
                        'data': pdata,
                        'borderWidth': 2,
                        'spacing': 1
                    }]
    if error:
        flash(error, 'error')
    return render_template('dashboard/sales.html',payment_methods=list(payment_methods.keys()), payment_methods_data=  payment_methods_data)
