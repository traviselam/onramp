"""Dispatchers implementing the OnRamp Server API.

Exports:
    Root: Root directoy
"""

#
# https://cherrypy.readthedocs.org/en/3.3.0/tutorial/REST.html
#

import pprint
import copy
import glob
import logging
import os
import json
import hashlib
import shutil
from multiprocessing import Process
from subprocess import call

import cherrypy
from configobj import ConfigObj
from Crypto import Random
from Crypto.Cipher import AES
from validate import Validator

import OnRampServer.onramppce as onramppce
import OnRampServer.onrampdb as onrampdb

class _ServerResourceBase:
    """Provide functionality needed by all OnRamp Server resource dispatchers.

    Class Attrs:
        exposed (bool): If True, resource is accessible via the Web.

    Instance Attrs
        conf (ConfigObj): Application config object.
        logger (logging.Logger): Pre-configured application logging instance.
        api_root (str): URL of application's api root.
        url_base (str): Base URL for the resource.

    Methods:
        JSON_response: Constructs JSON reponse from default and provided attrs.
        validate_JSON_request: Validates JSON request data.
    """
    exposed = True

    def __init__(self, conf):
        """Instantiate OnRamp Server Resource.

        Args:
            conf (ConfigObj): Application configuration object.
        """
        self.conf = conf
        self.logger = logging.getLogger('onramp')

        server = None
        if 'url_docroot' in conf['server'].keys():
            server = conf['server']['url_docroot']
        else:
            server = conf['server']['socket_host'] + ':' + str(conf['server']['socket_port'])

        self.url_base = (server + '/' + self.__class__.__name__.lower() + '/')
        self.api_root = (server + '/api/')

        # Define the Database - SQLite
        self.logger.debug("Connecting to the database")
        rtn = onrampdb.define_database(self.logger, 'sqlite', {'filename' : os.getcwd() + '/../tmp/onramp_sqlite.db'} )
        if rtn != 0:
            sys.exit(-1)

    def JSON_response(self, id=None, url=True, status_code=0,
                      status_msg='Success', **kwargs):
        """Construct JSON response from default and provided attrs.

        Kwargs:
            id: If not none, set response value for 'url' to the url for
                specific resource specified by id.
            url (bool): If false, set response value for 'url' to None.
            status_code (int): Status code of response.
            status_msg (str): Status message.
            **kwargs (dict): Key/value pairs to include in the JSON response.
        """
        self.logger.debug('KWARGS: %s' % str(kwargs))
        retval = {}
        retval['status_code'] = status_code
        retval['status_msg'] = status_msg
        if url:
            retval['url'] = self._build_url(id=id)
        else:
            retval['url'] = None
        retval['api_root'] = self.api_root
        retval.update(kwargs)
        return json.dumps(retval)

    def get_is_valid_fns(self):
        return {'user' : self.is_valid_user,
                'workspace' : self.is_valid_workspace,
                'pce' : self.is_valid_pce,
                'module' : self.is_valid_module,
                'job' : self.is_valid_job
                }

    def is_valid_user(self, user_id=None):
        if user_id is None:
            return False

        # TODO

        return True

    def is_valid_workspace(self, workspace_id=None):
        if workspace_id is None:
            return False
        # TODO
        #if int(workspace_id) is not 123:
        #    return False

        return True

    def is_valid_pce(self, pce_id=None):
        if pce_id is None:
            return False

        # TODO

        return True

    def is_valid_module(self, module_id=None):
        if module_id is None:
            return False

        # TODO

        return True

    def is_valid_job(self, job_id=None):
        if job_id is None:
            return False

        # TODO

        return True


########################################################
 
class Root(_ServerResourceBase):

    @cherrypy.popargs('user')
    def GET(self, id=None, **kwargs):
        self.logger.debug('Root.GET()')
        if id is not None:
            raise cherrypy.NotFound()

        #host = cherrypy.request.headers('Host')
        #host = cherrypy.request.headers.get('Host', None)
        #host = self.api_root
        #host = str(cherrypy.request.headers)
        return "OnRamp Server is running...\n"

class Users(_ServerResourceBase):

    # GET /users
    #     /users/:ID
    #     /users/:ID/workspaces
    #     /users/:ID/jobs
    #     /users/:ID/jobs?workspace=ID&pce=ID&module=ID
    @cherrypy.popargs('level')
    def GET(self, user_id=None, level=None, **kwargs):
        self.logger.debug('Users.GET()')

        allowed_levels = ["workspaces", "jobs"]
        allowed_search = ["workspace", "pce", "module"]
        valid_fns = self.get_is_valid_fns()

        debug = "All"
        ids = {}

        #
        # Parse the arguments
        #
        if user_id is not None:
            if valid_fns['user'](user_id) is False:
                raise cherrypy.HTTPError(400)
            debug = "Specific User " + user_id

        if level is not None:
            if level not in allowed_levels:
                raise cherrypy.NotFound()
            debug += " at " + level

        for key, value in kwargs.iteritems():
            if key not in allowed_search:
                raise cherrypy.HTTPError(400)
            if valid_fns[key](value) is False:
                raise cherrypy.HTTPError(400)

            ids[key] = value
            debug += "("+key+"="+value+")"


        self.logger.debug('Users.GET(): %s' % debug)

        #
        # Perform the correct operation
        #

        return "Users: %s\n" % debug

    #
    # POST /users/:ID
    #
    def POST(self, id=None, **kwargs):
        self.logger.debug('Users.POST()')

        allowed_search = ["name", "email"]

        for key, value in kwargs.iteritems():
            if key not in allowed_search:
                raise cherrypy.HTTPError(400)
            self.logger.debug("Users.POST(): %s=%s" % (key, value) )

        return "Users: \n"

class Workspaces(_ServerResourceBase):

    # GET /workspaces
    #     /workspaces/:ID
    #     /workspaces/:ID/doc
    #     /workspaces/:ID/users
    #     /workspaces/:ID/pcemodulepairs
    #     /workspaces/:ID/jobs
    #     /workspaces/:ID/jobs?user=ID&pce=ID&module=ID
    @cherrypy.popargs('level')
    def GET(self, workspace_id=None, level=None, **kwargs):
        self.logger.debug('Workspaces.GET()')

        allowed_levels = ["doc", "users", "pcemodulepairs", "jobs"]
        allowed_search = ["user", "pce", "module"]
        valid_fns = self.get_is_valid_fns()

        debug = "All"
        ids = {}

        #
        # Parse the arguments
        #
        if workspace_id is not None:
            if valid_fns['workspace'](workspace_id) is False:
                raise cherrypy.HTTPError(400)
            debug = "Specific Workspace " + workspace_id

        if level is not None:
            if level not in allowed_levels:
                raise cherrypy.NotFound()
            debug += " at " + level

        for key, value in kwargs.iteritems():
            if key not in allowed_search:
                raise cherrypy.HTTPError(400)
            if valid_fns[key](value) is False:
                raise cherrypy.HTTPError(400)

            ids[key] = value
            debug += "("+key+"="+value+")"


        self.logger.debug('Workspaces.GET(): %s' % debug)

        #
        # Perform the correct operation
        #

        return "Workspace: %s\n" % debug


class PCEs(_ServerResourceBase):

    # GET /pces
    #     /pces/:ID
    #     /pces/:ID/doc
    #     /pces/:ID/workspaces
    #     /pces/:ID/modules
    #     /pces/:ID/jobs
    #     /pces/:ID/jobs?user=ID&workspace=ID&module=ID
    @cherrypy.popargs('level')
    def GET(self, pce_id=None, level=None, **kwargs):
        self.logger.debug('PCEs.GET()')

        allowed_levels = ["doc", "workspaces", "modules", "jobs"]
        allowed_search = ["user", "workspace", "module"]
        valid_fns = self.get_is_valid_fns()

        debug = "All"
        ids = {}

        #
        # Parse the arguments
        #
        if pce_id is not None:
            if valid_fns['pce'](pce_id) is False:
                raise cherrypy.HTTPError(400)
            debug = "Specific PCE " + pce_id

        if level is not None:
            if level not in allowed_levels:
                raise cherrypy.NotFound()
            debug += " at " + level

        for key, value in kwargs.iteritems():
            if key not in allowed_search:
                raise cherrypy.HTTPError(400)
            if valid_fns[key](value) is False:
                raise cherrypy.HTTPError(400)

            ids[key] = value
            debug += "("+key+"="+value+")"


        self.logger.debug('PCEs.GET(): %s' % debug)

        #
        # Perform the correct operation
        #

        return "PCE: %s\n" % debug

class Modules(_ServerResourceBase):

    # GET /modules
    #     /modules/:ID
    #     /modules/:ID/doc
    #     /modules/:ID/pces
    #     /modules/:ID/jobs
    #     /modules/:ID/jobs?user=ID&workspace=ID&pce=ID
    @cherrypy.popargs('level')
    def GET(self, module_id=None, level=None, **kwargs):
        self.logger.debug('Modules.GET()')

        allowed_levels = ["doc", "pces", "jobs"]
        allowed_search = ["user", "workspace", "pce"]
        valid_fns = self.get_is_valid_fns()

        debug = "All"
        ids = {}

        #
        # Parse the arguments
        #
        if module_id is not None:
            if valid_fns['module'](module_id) is False:
                raise cherrypy.HTTPError(400)
            debug = "Specific Module " + module_id

        if level is not None:
            if level not in allowed_levels:
                raise cherrypy.NotFound()
            debug += " at " + level

        for key, value in kwargs.iteritems():
            if key not in allowed_search:
                raise cherrypy.HTTPError(400)
            if valid_fns[key](value) is False:
                raise cherrypy.HTTPError(400)

            ids[key] = value
            debug += "("+key+"="+value+")"


        self.logger.debug('Modules.GET(): %s' % debug)

        #
        # Perform the correct operation
        #

        return "Module: %s\n" % debug

class Jobs(_ServerResourceBase):

    # GET /jobs
    #     /jobs/:ID
    #     /jobs/:ID/data
    @cherrypy.popargs('level')
    def GET(self, job_id=None, level=None, **kwargs):
        self.logger.debug('Jobs.GET()')

        allowed_levels = ["data"]
        allowed_search = []
        valid_fns = self.get_is_valid_fns()

        debug = "All"
        ids = {}

        #
        # Parse the arguments
        #
        if job_id is not None:
            if valid_fns['job'](job_id) is False:
                raise cherrypy.HTTPError(400)
            debug = "Specific Job " + job_id

        if level is not None:
            if level not in allowed_levels:
                raise cherrypy.NotFound()
            debug += " at " + level

        for key, value in kwargs.iteritems():
            if key not in allowed_search:
                raise cherrypy.HTTPError(400)
            if valid_fns[key](value) is False:
                raise cherrypy.HTTPError(400)

            ids[key] = value
            debug += "("+key+"="+value+")"


        self.logger.debug('Jobs.GET(): %s' % debug)

        #
        # Perform the correct operation
        #

        return "Job: %s\n" % debug

    #
    # POST /jobs
    #
    def POST(self, id=None, **kwargs):
        self.logger.debug('Jobs.POST()')

        allowed_search = ["foo", "bar"]

        for key, value in kwargs.iteritems():
            if key not in allowed_search:
                raise cherrypy.HTTPError(400)
            self.logger.debug("Jobs.POST(): %s=%s" % (key, value) )

        return "Jobs: \n"

    #
    # DELETE /jobs/:ID
    #
    def DELETE(self, id=None, **kwargs):
        self.logger.debug('Jobs.DELETE()')

        if id is None:
            raise cherrypy.HTTPError(400)

        return "Jobs: "+id+"\n"

class Login(_ServerResourceBase):

    # POST /login
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def POST(self, id=None, **kwargs):
        prefix = '[POST /login]'
        self.logger.debug(prefix)

        rtn = {}
        rtn['status'] = 0
        rtn['status_message'] = 'Success'

        if not hasattr(cherrypy.request, "json"):
            self.logger.error(prefix + " No json data sent")
            raise cherrypy.HTTPError(400)

        data = cherrypy.request.json

        #
        # Make sure the required fields have been specified
        #
        allowed_search = ["username", "password"]
        for key in allowed_search:
            if key not in data:
                self.logger.error(prefix + " Missing key \"" + key + "\"")
                raise cherrypy.HTTPError(400, "Bad Request ...")

        #
        # Ask the database if this is a valid user
        #
        self.logger.info(prefix + " Attempt \"" + data["username"] + "\"")

        user_id = onrampdb.user_login( data["username"], data["password"])

        if user_id is not None:
            rtn['auth'] = {'id' : user_id }
            self.logger.info(prefix + " Attempt \"" + data["username"] + "\" Success")
        else:
            self.logger.info(prefix + " Attempt \"" + data["username"] + "\" Failed")
            raise cherrypy.HTTPError(401)

        #
        # Tell the user
        #

        return rtn

class Admin(_ServerResourceBase):

    # GET
    #      /admin/pce/:PCEID
    #      /admin/pce/:PCEID/module/:MODULEID
    @cherrypy.popargs('level', 'pce_id', 'mlevel', 'module_id')
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def GET(self, level=None, pce_id=None, mlevel=None, module_id=None, **kwargs):
        prefix = '[GET /admin/]'
        self.logger.debug(prefix)

        debug = "Any"

        if level != "pce":
            raise cherrypy.NotFound()

        prefix = '[GET /admin/pce]'

        if pce_id is None:
            raise cherrypy.NotFound()
        elif self.is_valid_pce(pce_id) is False:
            prefix = '[GET /admin/pce/'+str(pce_id)+']'
            raise cherrypy.HTTPError(400)

        self.logger.debug(prefix)
        debug = "PCE="+pce_id

        if mlevel is not None:
            if module_id is None:
                raise cherrypy.NotFound()
            elif self.is_valid_module(module_id) is False:
                raise cherrypy.HTTPError(400)
            debug += ", Module="+module_id

        self.logger.debug(prefix + ' %s' % debug )

        return "Admin: %s\n" % debug

    # POST / DELETE / PUT
    #      /admin/user
    #      /admin/module
    #      /admin/workspace
    #      /admin/workspace/:WORKSPACEID/user/:USERID
    #      /admin/workspace/:WORKSPACEID/pcemodulepairs/:PCEID/:MODULEID
    #      /admin/pce
    #      /admin/pce/:PCEID/module/:MODULEID
    @cherrypy.popargs('level1', 'level1_id', 'level2', 'level2_id', 'level3_id')
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def POST(self, level1=None, level1_id=None, level2=None, level2_id=None, level3_id=None, **kwargs):
        prefix = '[POST /admin/]'
        self.logger.debug(prefix)

        rtn = {}
        rtn['status'] = 0
        rtn['status_message'] = 'Success'

        allowed_level1 = {'user' : self.process_user,
                          'module' : self.process_module,
                          'workspace' : self.process_workspace,
                          'pce' : self.process_pce,
                          }
        debug = "Any"

        #
        # Level 1 is required
        #
        if level1 is None:
            raise cherrypy.NotFound()
        elif level1 not in allowed_level1.keys():
            raise cherrypy.HTTPError(400)

        if not hasattr(cherrypy.request, "json"):
            self.logger.error(prefix + " No json data sent")
            raise cherrypy.HTTPError(400)

        data = cherrypy.request.json

        debug = level1

        if level1 == "user" or level1 == "module":
            rdata = allowed_level1[level1]("POST", data, level1_id, kwargs)
        else:
            rdata = allowed_level1[level1]("POST", data, level1_id, level2, level2_id, level3_id, kwargs)

        rtn[level1] = rdata

        return rtn

    def process_user(self, type, data, user_id=None, kwargs=None):
        prefix = '['+type+' /admin/user]'
        rdata = {}

        #
        # Adding a new user
        #
        if user_id is None:
            self.logger.info(prefix + " Adding \"" + data["username"] + "\"")
            user_id = onrampdb.user_lookup( data["username"] )
            if user_id is not None:
                rdata['exists'] = True
            else:
                user_id = onrampdb.user_add( data["username"], data["password"] )
                if user_id is None:
                    raise cherrypy.HTTPError(400)
                rdata['exists'] = False
            rdata['id'] = user_id

        self.logger.debug(prefix + ' process_user(%s, %s)' % (type, user_id))

        return rdata

    def process_module(self, type, data, module_id=None, kwargs=None):
        self.logger.debug('Admin: process_module(%s, %s)' % (type, module_id))
        return True

    def process_workspace(self, type, data, workspace_id=None, level2=None, level2_id=None, level3_id=None, kwargs=None):
        self.logger.debug('Admin: process_workspace(%s, %s)' % (type, workspace_id))
        return True

    def process_pce(self, type, data, pce_id=None, level2=None, level2_id=None, level3_id=None, kwargs=None):
        self.logger.debug('Admin: process_pce(%s, %s)' % (type, pce_id))
        return True
