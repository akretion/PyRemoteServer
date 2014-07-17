# -*- coding: utf-8 -*-
###############################################################################
#
#   PyRemote
#   Copyright (C) 2014 Akretion (http://www.akretion.com).
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################


from flask import Flask, render_template, url_for, redirect
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from wtforms import IntegerField
from wtforms.validators import DataRequired
import subprocess
import psutil
import os
import signal

def create_app(config=None):
    app = Flask(__name__)
    Bootstrap(app)
    app.config.from_pyfile(config)
    return app

conf_file = '%s/config.cfg' % os.path.dirname(os.path.realpath(__file__))
app = create_app(conf_file)


class HelpForm(Form):
    server_port = IntegerField('ID support', validators=[DataRequired()], default=22)
    redirect_port = IntegerField('ID client', validators=[DataRequired()], default=22222)


class AutoSSH(object):

    def get_pid(self):
        for p in psutil.process_iter():
            if "autossh" in str(p.name):
                return p.pid
        return None

    def start(self, server_port=22, redirect_port=22222):
        app.logger.info('start autossh ...')
        # WARNING: this code is totally unsecure
        # but as we run on a rasbperry accesible
        # only on the local network, for now we don't care
        subprocess.call((
            "export AUTOSSH_GATETIME=0; "
            "export AUTOSSH_PORT=0; "
            "/usr/lib/autossh/autossh -vv -f -- -i ~/.ssh/id_rsa "
            "-o 'ControlPath none' -R %s:localhost:%s %s -N > ~/autossh.log"
            ) % (server_port, redirect_port, app.config['SUPPORT_SERVER']),
            shell=True
            )
        return True

    def stop(self):
        pid = self.get_pid()
        os.kill(pid, signal.SIGTERM)
        return True

    def restart(self, pid):
        app.logger.info('restart proxy ...')
        self.stop(pid)
        app.logger.info('waiting for stopping proxy ...')
        sleep(7);
        self.start()
        return True

autossh = AutoSSH()
sshkey = open("/home/sebastien/.ssh/id_rsa.pub").read()

@app.route('/', methods=['GET', 'POST'])
def index():
    form = HelpForm();
    if form.validate_on_submit():
        autossh.start(form.data['server_port'], form.data['redirect_port'])
        return render_template('running.html')
    if autossh.get_pid():
        return render_template('running.html')
    else:
        return render_template('index.html', form=form, sshkey=sshkey)

@app.route('/stop', methods=['GET'])
def stop():
    autossh.stop()
    return redirect('/')

if __name__ == '__main__':
    app.run(port=5555, host='0.0.0.0')
