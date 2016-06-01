#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
The automata (finite state machine) referenced by the monkey.
"""

import os, sys, json, posixpath, time, codecs, random, logging
from os.path import relpath
import networkx
from dom_analyzer import DomAnalyzer
from hashUtil import Hash

class Automata:
    def __init__(self, configuration):
        self._states = []
        self._edges = []
        self._initial_state = None
        self._current_state = None
        self._automata_fname = 'automata.json'
        self.configuration = configuration
        # make a hashmap with 19 blocks for states
        self._hash = Hash(19, self, self.configuration)
        # make a graph for counting paths
        self._graph = networkx.DiGraph()

    def get_current_state(self):
        return self._current_state

    def get_initial_state(self):
        return self._initial_state

    def get_states(self):
        return self._states

    def get_edges(self):
        return self._edges

    def set_initial_state(self, state):
        if not state.get_id():
            state.set_id( str(len( self._states )) )
        is_new, state_id  = self._hash.put(state)
        if is_new:
            self._states.append(state)
            self._initial_state = state
            self._current_state = state
            self._graph.add_node(state)
        else:
            state = self.get_state_by_id(state_id)
        return is_new, state

    def add_state(self, state):
        if not state.get_id():
            state.set_id( str(len( self._states )) )            
        is_new, state_id = self._hash.put(state)
        #change state if not new
        if is_new:
            self._states.append(state)
            self._graph.add_node(state)
        else:
            state = self.get_state_by_id(state_id)
        return state, is_new

    def change_state(self, state):
        self._current_state = state

    def add_edge(self, edge, state_to):
        edge.set_state_to( state_to )
        edge.set_id( str(len( self._edges )) )
        self._edges.append(edge)
        self._graph.add_edge( self.get_state_by_id(edge.get_state_from()),
                              self.get_state_by_id(edge.get_state_to()) )

    def get_state_by_id(self, sid):
        for s in self._states:
            if s.get_id() == sid:
                return s
        return None

    def get_edge_by_from_to(self, state_from, state_to ):
        for edge in self._edges:
            if edge.get_state_from() == state_from and edge.get_state_to() == state_to:
                return edge
        return None

    def get_shortest_path(self, target):
        shortest_paths = list( networkx.shortest_simple_paths(self._graph, self._initial_state, target) )
        shortest_path = shortest_paths[0]
        edges = []
        for i in range(len(shortest_path)-1):
            edges.append( self.get_edge_by_from_to( shortest_path[i].get_id(),
                                                    shortest_path[i+1].get_id() ) )
        return edges

    def get_all_simple_states_and_traces(self):
        traces=[]
        for end_state in self._states:
            if end_state.get_clickables():
                # has clickable => not end
                continue
            for state_trace in networkx.all_simple_paths(self._graph,
                            source=self._initial_state, target=end_state ):
                edge_trace = []
                for i in range(len(state_trace)-1):
                    edge_trace.append( self.get_edge_by_from_to( state_trace[i].get_id(),
                                                                 state_trace[i+1].get_id() ) )
                traces.append( (state_trace, edge_trace) )
        return traces

    def save_dom(self, state):
        try:
            #make dir for each state
            state_dir = os.path.join( self.configuration.get_abs_path('dom'), state.get_id() )
            if not os.path.isdir(state_dir):
                os.makedirs(state_dir)

            iframe_key_dict = { 'num': 0 }
            for stateDom in state.get_dom_list(self.configuration):
                iframe_key = ';'.join(stateDom['iframe_path']) if stateDom['iframe_path'] else None
                #make new dir for iframe
                if stateDom['iframe_path']:
                    iframe_key_dict['num'] += 1
                    iframe_key_dict[ str(iframe_key_dict['num']) ] = { 'path' : stateDom['iframe_path'], 'url': stateDom['url'] }
                    dom_dir = os.path.join( self.configuration.get_abs_path('dom'), state.get_id(), str(iframe_key_dict['num']) )
                    if not os.path.isdir(dom_dir):
                        os.makedirs(dom_dir)
                else:
                    iframe_key_dict['basic'] = { 'url' : stateDom['url'] }
                    dom_dir = os.path.join( self.configuration.get_abs_path('dom'), state.get_id() )

                with codecs.open( os.path.join( dom_dir, state.get_id()+'.txt'),            'w', encoding='utf-8' ) as f:
                    f.write( stateDom['dom'] )
                with codecs.open( os.path.join( dom_dir, state.get_id()+'_nor.txt'),        'w', encoding='utf-8' ) as f:
                    f.write( DomAnalyzer.normalize( stateDom['dom'] ) )
                with codecs.open( os.path.join( dom_dir, state.get_id()+'_inputs.txt'),     'w', encoding='utf-8' ) as f:
                    json.dump(state.get_inputs_json( iframe_key ),               f, indent=2, sort_keys=True, ensure_ascii=False)
                with codecs.open( os.path.join( dom_dir, state.get_id()+'_selects.txt'),    'w', encoding='utf-8' ) as f:
                    json.dump(state.get_selects_json(iframe_key ),               f, indent=2, sort_keys=True, ensure_ascii=False)
                with codecs.open( os.path.join( dom_dir, state.get_id()+'_radios.txt'),     'w', encoding='utf-8' ) as f:
                    json.dump(state.get_radios_json(iframe_key ),                f, indent=2, sort_keys=True, ensure_ascii=False)
                with codecs.open( os.path.join( dom_dir, state.get_id()+'_checkboxes.txt'), 'w', encoding='utf-8' ) as f:
                    json.dump(state.get_checkboxes_json(iframe_key ),            f, indent=2, sort_keys=True, ensure_ascii=False)
                with codecs.open( os.path.join( dom_dir, state.get_id()+'_clicks.txt'),     'w', encoding='utf-8' ) as f:
                    json.dump(state.get_candidate_clickables_json( iframe_key ), f, indent=2, sort_keys=True, ensure_ascii=False)

            with codecs.open( os.path.join( state_dir, 'iframe_list.json'),  'w', encoding='utf-8' ) as f:
                json.dump( iframe_key_dict, f, indent=2, sort_keys=True, ensure_ascii=False)

            """
            TODO: turn TempFile stateDom into FilePath stateDom
            """
            state.clear_dom()

        except Exception as e:  
            logging.error(' save dom : %s \t\t__from automata.py save_dom()', str(e))

    def save_state(self, state, depth):
        candidate_clickables = {}       
        inputs = {}
        selects = {}
        checkboxes = {}
        radios = {}
        for stateDom in state.get_dom_list(self.configuration):
            iframe_path_list = stateDom['iframe_path']
            dom = stateDom['dom']
            # define iframe_key of dom dict
            iframe_key = ';'.join(iframe_path_list) if iframe_path_list else None

            candidate_clickables[iframe_key] = DomAnalyzer.get_candidate_clickables_soup(dom)
            inputs[iframe_key] = DomAnalyzer.get_inputs(dom)
            selects[iframe_key] = DomAnalyzer.get_selects(dom)
            checkboxes[iframe_key] = DomAnalyzer.get_checkboxes(dom)
            radios[iframe_key] = DomAnalyzer.get_radios(dom)

        state.set_candidate_clickables(candidate_clickables)
        state.set_inputs(inputs)
        state.set_selects(selects)
        state.set_checkboxes(checkboxes)
        state.set_radios(radios)
        state.set_depth(depth)

        self.save_dom(state)

    def save_state_shot(self, executor, state):
        path = os.path.join(self.configuration.get_abs_path('state'), state.get_id() + '.png')
        executor.get_screenshot(path)

    def save_traces(self, configuration):
        traces = self.get_all_simple_states_and_traces()
        traces_data = {
            'traces': []
        }
        for state_trace, edge_trace in traces:
            trace_data = {
                'states':[],
                'edges':[]
            }
            for state in state_trace:
                trace_data['states'].append(state.get_simple_state_json(configuration))
            for edge in edge_trace:                
                trace_data['edges'].append(edge.get_edge_json())
            traces_data['traces'].append(trace_data)

        with codecs.open(os.path.join(configuration.get_abs_path('root'), configuration.get_traces_fname()), 'w', encoding='utf-8' ) as f:
            json.dump(traces_data, f, indent=2, sort_keys=True, ensure_ascii=False)

    def save_automata(self, configuration, automata_fname=None):
        automata_fname = configuration.get_automata_fname() if not automata_fname else automata_fname
        data = {
            'state': [],
            'edge': [], 
            # the prefix used in ids given by our monkey
            'id_prefix': DomAnalyzer.serial_prefix
        }
        for state in self._states:
            data['state'].append(state.get_state_json(configuration))
        for edge in self._edges:
            data['edge'].append(edge.get_edge_json())

        with codecs.open(os.path.join(configuration.get_abs_path('root'), configuration.get_automata_fname()), 'w', encoding='utf-8' ) as f:
            json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)


class State:
    def __init__(self, dom_list, url):
        self._id = None
        #list of Statedom( dom, iframe )
        self._dom_list = dom_list
        self._prev_states = []
        self._clickables = {}
        self._url = url
        self._depth = 0
        #=============================================================================================
        #Diff: inputs information save in state, indiviual to clickables, add normalize_dom
        self._inputs = {} #dict [iframes] of inputs
        self._selects = {}
        self._candidate_clickables = {}
        self._radios = {}
        self._checkboxes = {}
        #=============================================================================================

    def add_clickable(self, clickable, iframe_key):
        # check if the clickable is duplicated
        if iframe_key in self._clickables.keys():
            if clickable.get_id():
                for c in self._clickables[iframe_key]:
                    if c.get_id() == clickable.get_id():
                        return False
            else:
                for c in self._clickables[iframe_key]:
                    if c.get_xpath() == clickable.get_xpath():
                        return False
            self._clickables[iframe_key].append( clickable )
        else:
            self._clickables[iframe_key] = [clickable]
        return True

    def get_clickable_by_id(self, c_id):
        for iframe_key in self._clickables.keys():
            for c in self._clickables[iframe_key]:
                if c.get_id() == c_id:
                    return c
        return None

    def get_clickables(self):
        return self._clickables

    def get_all_clickables_json(self):
        note = []
        for iframe_key in self._clickables.keys():
            iframe_data = {
                'clickables': []
            }
            iframe_data['iframe_list'] = iframe_key.split(';') if iframe_key else None
            for clickable in self._clickables[iframe_key]:
                clickable_data = {
                    'id': clickable.get_id(),
                    'name': clickable.get_name(),
                    'xpath': clickable.get_xpath(),
                    'tag': clickable.get_tag()
                }
                iframe_data['clickables'].append(clickable_data)
            note.append(iframe_data)
        return note

    def set_id(self, state_id):
        self._id = state_id

    def get_id(self):
        return self._id

    def add_prev_state(self, state):
        if state not in self._prev_states:
            self._prev_states.append(state)

    def get_prev_states(self):
        return self._prev_states

    def __str__(self):
        return 'state id: %s, prev states: %s, clickables: %s' % \
               (self._id, self._prev_states, len(self._clickables))

    def set_inputs(self, inputs):
        self._inputs = inputs

    def get_inputs(self, iframe_key):
        return self._inputs[iframe_key]

    def get_inputs_json(self, iframe_key):
        inputs_data = { 'inputs': [] }
        inputs_data['iframe_list'] = iframe_key.split(';') if iframe_key else None
        for my_input in self._inputs[iframe_key]:
            inputs_data['inputs'].append( {
                'id'   : my_input.get_id(),
                'name' : my_input.get_name(),
                'xpath': my_input.get_xpath(),
                'type' : my_input.get_type(),
            } ) 
        return inputs_data

    def get_all_inputs(self):
        return self._inputs 

    def get_all_inputs_json(self):
        note = []
        for iframe_key in self._inputs.keys():
            iframe_data = {
                'inputs': []
            }
            iframe_data['iframe_list'] = iframe_key.split(';') if iframe_key else None
            for my_input in self._inputs[iframe_key]:
                iframe_data['inputs'].append( {
                    'id'   : my_input.get_id(),
                    'name' : my_input.get_name(),
                    'xpath': my_input.get_xpath(),
                    'type' : my_input.get_type(),
                } ) 
            note.append(iframe_data)
        return note

    def set_selects(self, selects):
        self._selects = selects

    def get_selects(self, iframe_key):
        return self._selects[iframe_key]

    def get_selects_json(self, iframe_key):
        selects_data = { 'selects': [] }
        selects_data['iframe_list'] = iframe_key.split(';') if iframe_key else None
        for my_select in self._selects[iframe_key]:
            selects_data['selects'].append( {
                'id'   : my_select.get_id(),
                'name' : my_select.get_name(),
                'xpath': my_select.get_xpath(),
                'value': my_select.get_value()
            } )
        return selects_data

    def get_all_selects(self):
        return self._selects

    def get_all_selects_json(self):
        note = []
        for iframe_key in self._selects.keys():
            iframe_data = {
                'selects': []
            }
            iframe_data['iframe_list'] = iframe_key.split(';') if iframe_key else None
            for my_select in self._selects[iframe_key]:
                select_data = {
                    'id'   : my_select.get_id(),
                    'name' : my_select.get_name(),
                    'xpath': my_select.get_xpath(),
                    'value': my_select.get_value()
                }
                iframe_data['selects'].append(select_data) 
            note.append(iframe_data)
        return note

    def set_checkboxes(self, checkboxes):
        self._checkboxes = checkboxes

    def get_checkboxes(self, iframe_key):
        return self._checkboxes[iframe_key]

    def get_checkboxes_json(self, iframe_key):
        checkboxes_data = { 'checkboxes': [] }
        checkboxes_data['iframe_list'] = iframe_key.split(';') if iframe_key else None
        for my_checkbox_field in self._checkboxes[iframe_key]:
            checkbox_field_data = {
                'checkbox_name': my_checkbox_field.get_checkbox_name(),
                'checkbox_list': []
            }
            for my_checkbox in my_checkbox_field.get_checkbox_list():
                checkbox_field_data['checkbox_list'].append( {
                    'id'   : my_checkbox.get_id(),
                    'name' : my_checkbox.get_name(),
                    'xpath': my_checkbox.get_xpath(),
                    'value': my_checkbox.get_value()
                } )
            checkboxes_data['checkboxes'].append(checkbox_field_data)
        return checkboxes_data 

    def get_all_checkboxes(self):
        return self._checkboxes

    def get_all_checkboxes_json(self):
        note = []
        for iframe_key in self._checkboxes.keys():
            iframe_data = {
                'checkboxes': []
            }
            iframe_data['iframe_list'] = iframe_key.split(';') if iframe_key else None
            for my_checkbox_field in self._checkboxes[iframe_key]:
                checkbox_field_data = {
                    'checkbox_name': my_checkbox_field.get_checkbox_name(),
                    'checkbox_list': []
                }
                for my_checkbox in my_checkbox_field.get_checkbox_list():
                    checkbox_field_data['checkbox_list'].append( {
                        'id'   : my_checkbox.get_id(),
                        'name' : my_checkbox.get_name(),
                        'xpath': my_checkbox.get_xpath(),
                        'value': my_checkbox.get_value()
                    } )
                iframe_data['checkboxes'].append(checkbox_field_data)  
            note.append(iframe_data)
        return note

    def set_radios(self, radios):
        self._radios = radios

    def get_radios(self, iframe_key):
        return self._radios[iframe_key]

    def get_radios_json(self, iframe_key):
        radios_data = { 'radios': [] }
        radios_data['iframe_list'] = iframe_key.split(';') if iframe_key else None
        for my_radio_field in self._radios[iframe_key]:
            radio_field_data = {
                'radio_name': my_radio_field.get_radio_name(),
                'radio_list': []
            }
            for my_radio in my_radio_field.get_radio_list():
                radio_field_data['radio_list'].append( {
                    'id'   : my_radio.get_id(),
                    'name' : my_radio.get_name(),
                    'xpath': my_radio.get_xpath(),
                    'value': my_radio.get_value()
                } )
            radios_data['radios'].append(radio_field_data)
        return radios_data

    def get_all_radios(self):
        return self._radios

    def get_all_radios_json(self):
        note = []
        for iframe_key in self._radios.keys():
            iframe_data = {
                'radios': []
            }
            iframe_data['iframe_list'] = iframe_key.split(';') if iframe_key else None
            for my_radio_field in self._radios[iframe_key]:
                radio_field_data = {
                    'radio_name': my_radio_field.get_radio_name(),
                    'radio_list': []
                }
                for my_radio in my_radio_field.get_radio_list():
                    radio_data = {
                        'id'   : my_radio.get_id(),
                        'name' : my_radio.get_name(),
                        'xpath': my_radio.get_xpath(),
                        'value': my_radio.get_value()
                    }
                    radio_field_data['radio_list'].append(radio_data)
                iframe_data['radios'].append(radio_field_data) 
            note.append(iframe_data)
        return note

    def set_candidate_clickables(self, candidate_clickables):
        self._candidate_clickables = candidate_clickables

    def get_candidate_clickables(self, iframe_key):
        return self._candidate_clickables[iframe_key]

    def get_candidate_clickables_json(self, iframe_key):
        candidate_clickables_data = { 'candidate_clickables': [] }
        candidate_clickables_data['iframe_list'] = iframe_key.split(';') if iframe_key else None
        for c, xpath in self._candidate_clickables[iframe_key]:
            candidate_clickable = {}
            candidate_clickable['id'] = c['id'] if c.has_attr('id') else None
            candidate_clickable['name'] = c['name'] if c.has_attr('name') else None
            candidate_clickable['xpath'] = xpath
            candidate_clickable['tag'] = c.name
            candidate_clickables_data['candidate_clickables'].append(candidate_clickable)
        return candidate_clickables_data

    def get_all_candidate_clickables(self):
        return self._candidate_clickables

    def get_all_candidate_clickables_json(self):
        note = []
        for iframe_key in self._candidate_clickables.keys():
            iframe_data = {
                'candidate_clickables': []
            }
            iframe_data['iframe_list'] = iframe_key.split(';') if iframe_key else None
            for c, xpath in self._candidate_clickables[iframe_key]:
                candidate_clickable = {}
                candidate_clickable['id'] = c['id'] if c.has_attr('id') else None
                candidate_clickable['name'] = c['name'] if c.has_attr('name') else None
                candidate_clickable['xpath'] = xpath
                candidate_clickable['tag'] = c.name
                iframe_data['candidate_clickables'].append(candidate_clickable)
            note.append(iframe_data)
        return note

    def get_dom_list(self, configuration):
        if not self._dom_list:
            dom_list = []

            # load basic dom
            dom_path = os.path.join( configuration.get_abs_path('dom'), self._id, self._id+'.txt' )
            if not os.path.exists(dom_path):
                return [ { 'url': self._url, 'dom': "", 'iframe_path': None } ]

            with codecs.open( dom_path, 'r', encoding='utf-8') as f:
                dom_list.append( { 'url': self._url, 'dom': f.read(), 'iframe_path': None } )

            # check and load iframe dom
            list_dir = os.path.join( configuration.get_abs_path('dom'), self._id, 'iframe_list.json' )
            if os.path.exists(list_dir):
                with codecs.open( list_dir, 'r', encoding='utf-8' ) as f:
                    list_json = json.load(f)
                for i in range(list_json['num']):
                    dom_path = os.path.join( configuration.get_abs_path('dom'), self._id, str(i), self._id+'.txt' )
                    if os.path.exists(dom_path):
                        with codecs.open( dom_path, 'r', encoding='utf-8') as f:
                            dom_list.appens( { 'url': list_json[str(i+1)]['url'] , 'dom': f.read(), 'iframe_path': list_json[str(i+1)]['path'] } )
            return dom_list
        else:
            return self._dom_list

    def get_basic_dom(self, configuration):
        if not self._dom_list:
            dom_path = os.path.join( configuration.get_abs_path('dom'), self._id, self._id+'.txt' )
            if os.path.exists(dom_path):
                with codecs.open( dom_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return ""
        else:
            for stateDom in self._dom_list:
                if not stateDom['iframe_path']:
                    return stateDom['dom']
            return ""

    def get_dom(self, configuration, iframe_key):
        if not iframe_key:
            return self.get_basic_dom()
        if not self._dom_list:
            list_dir = os.path.join( configuration.get_abs_path('dom'), state.get_id(), 'iframe_list.json' )
            if os.path.exists(list_dir):
                with codecs.open( list_dir, 'r', encoding='utf-8' ) as f:
                    list_json = json.load(f)
                for i in range(list_json['num']):
                    if ';'.join( list_json[str(i+1)]['path'] ) == iframe_key:
                        dom_path = os.path.join( configuration.get_abs_path('dom'), self._id, str(i+1), self._id+'.txt' )
                        if os.path.exists(dom_path):
                            with codecs.open( dom_path, 'r', encoding='utf-8') as f:
                                return f.read()
                        else:
                            return ""
                        break
                return ""
            else:
                return ""
        else:
            for stateDom in self._dom_list:
                if not iframe_key and not stateDom['iframe_path']:
                    return stateDom['dom']
                elif ';'.join(stateDom['iframe_path']) == iframe_key:
                    return stateDom['dom']
            return ""

    def get_all_dom(self, configuration):
        if not self._dom_list:
            dom_list = self.get_dom_list(configuration)
            dom = [ stateDom['dom'] for stateDom in dom_list ]
            dom = "\n".join(dom)
            return dom
        else:
            dom = [ stateDom['dom'] for stateDom in self._dom_list ]
            dom = "\n".join(dom)
            return dom

    def get_all_normalize_dom(self, configuration):
        if not self._dom_list:
            dom_list = self.get_dom_list(configuration)
            dom = [ DomAnalyzer.normalize( stateDom['dom'] ) for stateDom in dom_list ]
            dom = "\n".join(dom)
            return dom
        else:
            dom = [ DomAnalyzer.normalize( stateDom['dom'] ) for stateDom in self._dom_list ]
            dom = "\n".join(dom)
            return dom

    def clear_dom(self):
        self._dom_list = None

    def set_url(self, url):
        self._url = url

    def get_url(self):
        return self._url

    def set_depth(self, depth):
        self._depth = depth

    def get_depth(self):
        return self._depth

    def get_state_json(self, configuration):
        state_data = {
            'id': self._id,
            'url': self._url,
            'depth': self._depth,
            # output unix style path for website: first unpack dirs in get_path('dom'),
            # and then posixpath.join them with the filename
            'dom_path': posixpath.join(
                            posixpath.join(
                                *(relpath(
                                    configuration.get_path('dom'),
                                    configuration.get_path('root')
                                    ).split(os.sep) ) ), self._id + '.txt' ),
            'img_path': posixpath.join(
                            posixpath.join(
                                *(relpath(
                                    configuration.get_path('state'),
                                    configuration.get_path('root')
                                    ).split(os.sep) ) ), self._id  + '.png' ),
            'clickable': self.get_all_clickables_json(),
            'inputs': self.get_all_inputs_json(),
            'selects': self.get_all_selects_json(),
            'radios': self.get_all_radios_json(),
            'checkboxes': self.get_all_checkboxes_json()
        }
        return state_data

    def get_simple_state_json(self, configuration):
        state_data = {
            'id': self._id,
            'url': self._url,
            'dom_path': posixpath.join(
                            posixpath.join(
                                *(relpath(
                                    configuration.get_path('dom'),
                                    configuration.get_path('root')
                                    ).split(os.sep) ) ), self._id + '.txt' ),
            'img_path': posixpath.join(
                            posixpath.join(
                                *(relpath(
                                    configuration.get_path('state'),
                                    configuration.get_path('root')
                                    ).split(os.sep) ) ), self._id  + '.png' ),
            'depth': self._depth
        }
        return state_data
        
class Edge:
    def __init__(self, state_from, state_to, clickable, \
                 inputs, selects, checkboxes, radios, iframe_key, cost = 1):
        self._id = None
        self._state_from = state_from
        self._state_to = state_to
        self._clickable = clickable
        self._inputs = inputs
        self._selects = selects
        self._checkboxes = checkboxes
        self._radios = radios
        self._iframe_list = None if not iframe_key \
            else iframe_key if type(iframe_key) == type([]) else iframe_key.split(';')

    def set_id(self, edge_id):
        self._id = edge_id

    def get_id(self):
        return self._id

    def get_state_from(self):
        return self._state_from

    def set_state_from(self, state_from):
        self._state_from = state_from

    def get_state_to(self):
        return self._state_to

    def set_state_to(self, state_to):
        self._state_to = state_to

    def set_state_to(self, state):
        self._state_to = state

    def get_clickable(self):
        return self._clickable

    def get_inputs(self):
        return self._inputs

    def get_selects(self):
        return self._selects

    def get_checkboxes(self):
        return self._checkboxes

    def get_radios(self):
        return self._radios

    def get_iframe_list(self):
        return self._iframe_list

    def get_copy(self):
        copy_edge = Edge( self._state_from, self._state_to, self._clickable.get_copy(),
                        [ i.get_copy() for i in self._inputs ], [ s.get_copy() for s in self._selects ],
                        [ c.get_copy() for c in self._checkboxes ], [ r.get_copy() for r in self._radios ],
                        self._iframe_list )
        copy_edge.set_id( self._id )
        return copy_edge       

    def get_edge_json(self):
        edge_data = {
            'from': self._state_from,
            'to': self._state_to,
            'id': self._id,
            'clickable': {
                'id': self._clickable.get_id(),
                'name': self._clickable.get_name(),
                'xpath': self._clickable.get_xpath(),
                'tag': self._clickable.get_tag()
            },
            'inputs': [],
            'selects': [],
            'checkboxes': [],
            'radios': [],
            'iframe_list': self._iframe_list
        }
        for my_input in self._inputs:
            input_data = {
                'id': my_input.get_id(),
                'name': my_input.get_name(),
                'xpath': my_input.get_xpath(),
                'type': my_input.get_type(),
                'value': my_input.get_value(),
                'info': my_input.get_mutation_info()
            }
            edge_data['inputs'].append(input_data)
        for select in self._selects:
            select_data = {
                'id': select.get_id(),
                'name': select.get_name(),
                'xpath': select.get_xpath(),
                'value': select.get_value(),
                'selected': select.get_selected()
            }
            edge_data['selects'].append(select_data)
        for checkbox_field in self._checkboxes:
            checkbox_field_data = {
                'checkbox_list': [],
                'checkbox_selected_list': checkbox_field.get_selected_list(),
                'checkbox_name': checkbox_field.get_checkbox_name()
            }
            for checkbox in checkbox_field.get_checkbox_list():
                checkbox_data = {
                    'id': checkbox.get_id(),
                    'name': checkbox.get_name(),
                    'xpath': checkbox.get_xpath(),
                    'value': checkbox.get_value()
                }
                checkbox_field_data['checkbox_list'].append(checkbox_data)
            edge_data['checkboxes'].append(checkbox_field_data)
        for radio_field in self._radios:
            radio_field_data = {
                'radio_list': [],
                'radio_selected': radio_field.get_selected(),
                'radio_name': radio_field.get_radio_name()
            }
            for radio in radio_field.get_radio_list():
                radio_data = {
                    'id': radio.get_id(),
                    'name': radio.get_name(),
                    'xpath': radio.get_xpath(),
                    'value': radio.get_value()
                }
                radio_field_data['radio_list'].append(radio_data)
            edge_data['radios'].append(radio_field_data)
        return edge_data