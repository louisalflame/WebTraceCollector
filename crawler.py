#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Module docstring
"""

import os, sys, json, posixpath, time, datetime, codecs, logging, random, copy, string
from abc import ABCMeta, abstractmethod
from automata import Automata, State, Edge
from visualizer import Visualizer
from dom_analyzer import DomAnalyzer
from configuration import MutationMethod
from mutation import Mutation
from bs4 import BeautifulSoup

if sys.version_info.major >= 3:
    from urllib.parse import urlparse
else:
    from urlparse import urlparse 

class Crawler:
    __metaclass__ = ABCMeta

    @abstractmethod
    def run(self):
        pass

#==============================================================================================================================
# Selenium Web Driver
#==============================================================================================================================
class SeleniumCrawler(Crawler):
    def __init__(self, configuration, executor, automata, databank, algorithm):
        self.configuration = configuration
        self.executor = executor
        self.automata = automata
        self.databank = databank

        #ALGO
        self.algorithm = algorithm
        self.algorithm.set_utility(self, configuration, executor, automata)
    
        #list of event:(state, clickable, inputs, selects, iframe_list)
        self.event_history = []

    def run(self):
        #start time
        self.time_start = time.time()

        self.executor.start()
        self.executor.goto_url()
        initial_state = self.get_initail_state()
        self.run_script_before_crawl(initial_state)
        self.crawl(1)
        return self.automata

    def run_algorithm(self):
        # repeat for trace_amount times
        for i in range( self.configuration.get_trace_amount() ):

            self.initial()

            while self.action_events:
                #check time
                if (time.time() - self.time_start) > self.configuration.get_max_time():
                    logging.info("|||| TIMO OUT |||| end crawl ")
                    break

                string = ''.join([ str(action['action']['clickable'].get_id())+str(action['depth'])+str(action['state'].get_id()) for action in self.action_events ])
                logging.info(' action_events : '+string )

                state, action, depth = self.get_next_action()
                self.change_state(state, action, depth)
                edge = self.trigger_action(state, action, depth)
                self.update_states(state, edge, action, depth)

            self.close()

            self.algorithm.save_traces()
            self.automata.save_automata(self.configuration.get_automata_fname())
            Visualizer.generate_html('web', os.path.join(self.configuration.get_path('root'), self.configuration.get_automata_fname()))
        
        return self.automata

    def initial(self):
        self.action_events = []
        #start time
        self.time_start = time.time()
        self.algorithm.prepare()

        current_state = self.automata.get_current_state()
        self.add_new_events(current_state, None, 0)

    def close(self):
        self.algorithm.end()
        self.executor.close()

    def get_next_action(self):
        event = self.algorithm.get_next_action( self.action_events )
        return event['state'], event['action'], event['depth']

    def change_state(self, state, action, depth):
        current_state = self.automata.get_current_state()

        if current_state != state:
            self.algorithm.change_state(state, action, depth)

        logging.info(' now depth(%s) - max_depth(%s); current state: %s', depth, self.configuration.get_max_depth(), state.get_id() )

    def trigger_action(self, state, action, depth):
        inputs     = state.get_copy_inputs( action['iframe_key'] )
        selects    = state.get_copy_selects(action['iframe_key'])
        checkboxes = state.get_copy_checkboxes(action['iframe_key'])
        radios     = state.get_copy_radios(action['iframe_key'])

        new_edge = Edge(state.get_id(), None, action['clickable'], inputs, selects, checkboxes, radios, action['iframe_key'] )
        self.algorithm.trigger_action( state, new_edge, action, depth )
        return new_edge

    def update_states(self, current_state, new_edge, action, depth):
        dom_list, url, is_same = self.is_same_state_dom(current_state)

        if is_same:
            self.algorithm.update_with_same_state(current_state, new_edge, action, depth, dom_list, url)

        if self.is_same_domain(url):
            logging.info(' |depth:%s state:%s| change dom to: %s', depth, current_state.get_id(), self.executor.get_url())

            # check if this is a new state
            temp_state = State(dom_list, url)
            new_state, is_newly_added = self.automata.add_state(temp_state)
            self.automata.add_edge(new_edge, new_state.get_id())
            # save this click edge
            current_state.add_clickable(action['clickable'], action['iframe_key'])
            self.automata.change_state(new_state)
            # depth GO ON
            depth += 1
            self.event_history.append(new_edge)

            if is_newly_added:
                self.algorithm.update_with_new_state(current_state, new_state, new_edge, action, depth, dom_list, url)

            else:
                self.algorithm.update_with_old_state(current_state, new_state, new_edge, action, depth, dom_list, url)

        else:
            self.algorithm.update_with_out_of_domain(current_state, new_edge, action, depth, dom_list, url)

    def add_new_events(self, state, prev_state, depth):
        self.algorithm.add_new_events(state, prev_state, depth)

    #=========================================================================================
    # BASIC CRAWL
    #=========================================================================================        
    def get_initail_state(self):
        logging.info(' get initial state')
        dom_list, url = self.executor.get_dom_list(self.configuration)
        initial_state = State( dom_list, url )
        is_new, state = self.automata.set_initial_state(initial_state)
        if is_new:
            self.automata.save_state(self.executor, initial_state, 0)
            self.automata.save_state_shot(self.executor, initial_state)
        else:
            self.automata.change_state(state)
        time.sleep(self.configuration.get_sleep_time())
        return state

    def run_script_before_crawl(self, prev_state):
        for edge in self.configuration.get_before_script():
            self.executor.click_event_by_edge(edge)
            self.event_history.append(edge)

            dom_list, url, is_same = self.is_same_state_dom(prev_state)
            if is_same:
                continue
            logging.info(' change dom to: ', self.executor.get_url())
            # check if this is a new state
            temp_state = State(dom_list, url)
            new_state, is_newly_added = self.automata.add_state(temp_state)
            self.automata.add_edge(edge, new_state.get_id())
            # save this click edge
            prev_state.add_clickable(edge.get_clickable(), edge.get_iframe_list())
            if is_newly_added:
                logging.info(' add new state %s of: %s', new_state.get_id(), url)
                self.automata.save_state(new_state, 0)
                self.automata.save_state_shot(self.executor, new_state)
                self.automata.change_state(new_state)
            prev_state = new_state

    #=============================================================================================
    # BACKTRACK
    #=============================================================================================
    def executor_backtrack( self, state, *executors ):
        # check if depth over max depth , time over max time
        if (time.time() - self.time_start) > self.configuration.get_max_time():
            logging.info("|||| TIMO OUT |||| end backtrack ")
            return

        #if url are same, guess they are just javascipt edges
        if executors[0].get_url() == state.get_url():
            #first, just refresh for javascript button
            logging.info('==<BACKTRACK> : try refresh')
            for exe in executors:
                exe.refresh()
            dom_list, url, is_same = self.is_same_state_dom(state)
            if is_same:
                return True

        #if can't , try go back form history
        logging.info('==<BACKTRACK> : try back_history ')
        for exe in executors:
            exe.back_history()
        dom_list, url, is_same = self.is_same_state_dom(state)
        if is_same:
            return True

        logging.info('==<BACKTRACK> : try back_script ')
        for exe in executors:
            exe.back_script()
        dom_list, url, is_same = self.is_same_state_dom(state)
        if is_same:
            return True

        #if can't , try do last edge of state history
        if self.event_history:
            logging.info('==<BACKTRACK> : try last edge of state history')
            for exe in executors:
                exe.forward_history()
                exe.click_event_by_edge( self.event_history[-1] )
            dom_list, url, is_same = self.is_same_state_dom(state)
            if is_same:
                return True

        #if can't, try go through all edge
        logging.info('==<BACKTRACK> : start form base ur')
        for exe in executors:
            exe.goto_url()
        dom_list, url, is_same = self.is_same_state_dom(state)
        if is_same:
            return True
        for edge in self.automata.get_shortest_path(state):
            for exe in executors:
                exe.click_event_by_edge( edge )
            dom_list, url, is_same = self.is_same_state_dom(state)
            if is_same:
                return True

        #if can't, restart and try go again
        logging.info('==<BACKTRACK> : retart driver')
        for exe in executors:
            exe.restart_app()
            exe.goto_url()
        dom_list, url, is_same = self.is_same_state_dom(state)
        if is_same:
            return True
        for edge in self.automata.get_shortest_path(state):
            for exe in executors:
                exe.click_event_by_edge( edge )
            #check again if executor really turn back. if not, sth error, stop
            state_to = self.automata.get_state_by_id( edge.get_state_to() )
            dom_list, url, is_same = self.is_same_state_dom(state_to)
            if not is_same:
                try:
                    debug_dir = os.path.join( self.configuration.get_abs_path('dom'), state.get_id(), 'debug' )
                    if not os.path.isdir(debug_dir):
                        os.makedirs(debug_dir)
                    err = State(dom_list, url)
                    with codecs.open( os.path.join( debug_dir, 'debug_origin_'+state_to.get_id()+'.txt' ), 'w', encoding='utf-8' ) as f:
                        f.write(state_to.get_all_dom(self.configuration))
                    with codecs.open( os.path.join( debug_dir, 'debug_restart_'+state_to.get_id()+'.txt' ), 'w', encoding='utf-8' ) as f:
                        f.write(err.get_all_dom(self.configuration))
                    with codecs.open( os.path.join( debug_dir, 'debug_origin_nor_'+state_to.get_id()+'.txt' ), 'w', encoding='utf-8' ) as f:
                        f.write( state_to.get_all_normalize_dom(self.configuration) )
                    with codecs.open( os.path.join( debug_dir, 'debug_restart_nor_'+state_to.get_id()+'.txt' ), 'w', encoding='utf-8' ) as f:
                        f.write( err.get_all_normalize_dom(self.configuration) )
                    logging.error('==<BACKTRACK> cannot traceback to %s \t\t__from crawler.py backtrack()', state_to.get_id() )
                except Exception as e:  
                    logging.info('==<BACKTRACK> save diff dom : %s', str(e))

        dom_list, url, is_same = self.is_same_state_dom(state)
        return is_same

    #=========================================================================================
    # EVENT
    #=========================================================================================
    def make_value(self, edge):
        rand = random.randint(0,1000)

        for input_field in edge.get_inputs():
            data_set = input_field.get_data_set(self.databank)
            #check data set
            value = data_set[ rand % len(data_set) ] if data_set \
                else ''.join( [random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(8)] )
            input_field.set_value(value)
            logging.info(" set input:%s value:%s "%(input_field.get_id(), value))

        for select_field in edge.get_selects():
            data_set = select_field.get_data_set(self.databank)
            #check data set
            selected = data_set[ rand % len(data_set) ] if data_set \
                else random.randint(0, len(select_field.get_value()))
            select_field.set_selected(selected)
            logging.info(" set select:%s value:%s "%(select_field.get_id(), selected))

        for checkbox_field in edge.get_checkboxes():
            data_set = checkbox_field.get_data_set(self.databank)
            #check data set
            selected_list = data_set[ rand % len(data_set) ].split('/') if data_set \
                else random.sample( range(len(checkbox_field.get_checkbox_list())),
                                    random.randint(0, len(checkbox_field.get_checkbox_list())) )
            checkbox_field.set_selected_list(selected_list)
            logging.info(" set checkbox:%s value:%s "%(checkbox_field.get_checkbox_name(), str(selected_list)))

        for radio_field in edge.get_radios():
            data_set = radio_field.get_data_set(self.databank)
            #check data set
            selected = data_set[ rand % len(data_set) ] if data_set \
                else random.randint(0, len(radio_field.get_radio_list()))
            radio_field.set_selected(selected)
            logging.info(" set radio:%s value:%s "%(radio_field.get_radio_name(), selected))

    #=========================================================================================
    # DECISION
    #=========================================================================================
    def is_same_domain(self, url):
        base_url = urlparse( self.configuration.get_url() )
        new_url = urlparse( url )
        if base_url.netloc == new_url.netloc:
            return True
        else:
            for d in self.configuration.get_domains():
                d_url = urlparse(d)
                if d_url.netloc == new_url.netloc:
                    return True
            return False

    def is_same_state_dom(self, cs):
        dom_list, url = self.executor.get_dom_list(self.configuration)
        cs_dom_list = cs.get_dom_list(self.configuration)
        if url != cs.get_url():
            return dom_list, url, False
        elif len( cs_dom_list ) != len( dom_list ):
            return dom_list, url, False
        else:
            for dom, cs_dom in zip(dom_list, cs_dom_list):
                if not dom == cs_dom:
                    return dom_list, url, False
        print ('same dom to: ', cs.get_id())
        return dom_list, url, True


#=========================================================================================
# TODO FOR MUTATION
#=========================================================================================

    def run_mutant(self):
        self.mutation_history = []
        self.mutation_cluster = {}
        self.mutation = Mutation(self.configuration.get_mutation_trace(), self.databank)
        self.mutation_traces = self.make_mutation_traces()
        
        # run a default trace for compare
        logging.info(" start run default trace")
        self.executor.start()
        self.executor.goto_url() 
        initial_state = self.get_initail_state()
        self.run_mutant_script(initial_state)
        self.close()

        # run all mutation traces
        logging.info(' total %d mutation traces ', len(self.mutation_traces))
        for n in xrange(len(self.mutation_traces)):
            logging.info(" start run number %d mutant trace", n)
            self.executor.start()
            self.executor.goto_url()    
            initial_state = self.get_initail_state()
            self.run_mutant_script(initial_state, self.mutation_traces[n])
            self.close()
        self.save_mutation_history()

    def make_mutation_traces(self):
        self.mutation.set_method(self.configuration.get_mutation_method())
        self.mutation.set_modes(self.configuration.get_mutation_modes())
        self.mutation.make_data_set()
        self.mutation.make_mutation_traces()
        # use a int to select sample of mutation traces
        mutation_traces = self.mutation.get_mutation_traces()
        #mutation_traces = random.sample( mutation_traces, 
        #    min( self.configuration.get_max_mutation_traces(), len(mutation_traces) ) )
        return mutation_traces

    def run_mutant_script(self, prev_state, mutation_trace=None):
        depth = 0
        edge_trace = []
        state_trace = [prev_state]
        # use -1 to mark
        cluster_value = prev_state.get_id() if mutation_trace else "-1"+prev_state.get_id()
        for edge in self.configuration.get_mutation_trace():
            new_edge = edge.get_copy()
            new_edge.set_state_from( prev_state.get_id() )
            if mutation_trace:
                self.make_mutant_value(new_edge, mutation_trace[depth])
            self.executor.click_event_by_edge(new_edge)
            self.event_history.append(new_edge)

            dom_list, url, is_same = self.is_same_state_dom(prev_state)
            if not is_same: 
                logging.info(' change dom to: %s', url)
            # check if this is a new state
            temp_state = State(dom_list, url)
            new_state, is_newly_added = self.automata.add_state(temp_state)
            self.automata.add_edge(new_edge, new_state.get_id())
            # save this click edge
            prev_state.add_clickable(edge.get_clickable(), new_edge.get_iframe_list())
            if is_newly_added:
                logging.info(' add new state %s of: %s', new_state.get_id(), url)
                self.automata.save_state(new_state, depth+1)
                self.automata.save_state_shot(self.executor, new_state)
                self.automata.change_state(new_state)
            # save the state, edge
            state_trace.append( new_state )
            edge_trace.append( new_edge )
            cluster_value += new_state.get_id()
            # prepare for next edge
            prev_state = new_state
            depth += 1

        self.mutation_history.append( (edge_trace, state_trace, cluster_value ) )
        logging.warning( [ c for e,s,c in  self.mutation_history ] )

    def cluster_mutation_trace(self):
        #then cluster other mutation traces
        for edge_trace, state_trace, cluster_value in self.mutation_history:
            if cluster_value in self.mutation_cluster:
                self.mutation_cluster[cluster_value].append( (edge_trace, state_trace) )
            else:
                self.mutation_cluster[cluster_value] = [ (edge_trace, state_trace) ]

    def save_mutation_history(self):
        self.cluster_mutation_trace()
        traces_data = {
            'method': self.configuration.get_mutation_method(),
            'traces': []
        }
        for cluster_key, mutation_traces in self.mutation_cluster.items():
            for edge_trace, state_trace in mutation_traces:
                trace_data = {
                    'edges':[],
                    'states':[],
                    'cluster_value': cluster_key
                }
                for edge in edge_trace:                
                    trace_data['edges'].append(edge.get_edge_json())
                for state in state_trace:
                    trace_data['states'].append(state.get_simple_state_json(self.configuration))
                if cluster_key.startswith('-1'):
                    traces_data['traces'].insert(0, trace_data)
                else:
                    traces_data['traces'].append(trace_data)

        with codecs.open(os.path.join(self.configuration.get_abs_path('root'), 'mutation_traces.json'), 'w', encoding='utf-8' ) as f:
            json.dump(traces_data, f, indent=2, sort_keys=True, ensure_ascii=False)
