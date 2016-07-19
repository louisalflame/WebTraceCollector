#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, json, codecs, logging, random
from abc import ABCMeta, abstractmethod
from dom_analyzer import DomAnalyzer
from executor import SeleniumExecutor

class AlgoCrawler:
    __metaclass__ = ABCMeta

    @abstractmethod
    def set_utility(self, crawler, configuration, executor, automata):
        pass

    @abstractmethod
    def prepare(self):
        pass

    @abstractmethod
    def add_new_events(self, state, prev_state, depth):
        pass  
        
    @abstractmethod
    def get_next_action(self, action_events):
        pass  

    @abstractmethod
    def trigger_action(self, state, new_edge, action, depth):
        pass  

    @abstractmethod
    def update_with_same_state(self, current_state, new_edge, action, depth, dom_list, url):
        pass  

    @abstractmethod
    def update_with_out_of_domain(self, current_state, new_edge, action, depth, dom_list, url):
        pass  

    @abstractmethod
    def update_with_new_state(self, current_state, new_state, new_edge, action, depth, dom_list, url):
        pass  

    @abstractmethod
    def update_with_old_state(self, current_state, new_state, new_edge, action, depth, dom_list, url):
        pass  

    @abstractmethod
    def save_traces(self):
        pass

    @abstractmethod
    def end(self):
        pass

class DFScrawler(AlgoCrawler):
    def __init__(self):
        pass

    def set_utility(self, crawler, configuration, executor, automata):
        self.crawler = crawler
        self.configuration = configuration
        self.executor = executor
        self.automata = automata

    def prepare(self):
        #executor
        self.executor.start()
        self.executor.goto_url()

        #initial state
        initial_state = self.crawler.get_initail_state()
        self.crawler.run_script_before_crawl(initial_state)

    def add_new_events(self, state, prev_state, depth):
        for clickables, iframe_key in DomAnalyzer.get_clickables(state, prev_state if prev_state else None):
            for clickable in clickables:
                self.crawler.action_events.append( {
                        'state'  : state,
                        'action' : { 'clickable':clickable, 'iframe_key':iframe_key },
                        'depth'  : depth,
                    } )

    def get_next_action(self, action_events):
        event = action_events.pop()
        return event

    def change_state(self, state, action, depth):
        logging.info('==========< BACKTRACK START >==========')
        logging.info('==<BACKTRACK> depth %s -> backtrack to state %s',depth ,state.get_id() )
        self.crawler.executor_backtrack(state, self.executor)
        logging.info('==========< BACKTRACK END   >==========')

    def trigger_action(self, state, new_edge, action, depth):
        logging.info(' |depth:%s state:%s| fire element in iframe(%s)', depth, state.get_id(), action['iframe_key'])
        self.crawler.make_value(new_edge)
        self.executor.click_event_by_edge(new_edge)

    def update_with_same_state(self, current_state, new_edge, action, depth, dom_list, url):
        # Do Nothing when same state
        return None

    def update_with_out_of_domain(self, current_state, new_edge, action, depth, dom_list, url):
        # back if state out of domain
        logging.info(' |depth:%s state:%s| out of domain: %s', depth, current_state.get_id(), url)
        logging.info('==========< BACKTRACK START >==========')
        logging.info('==<BACKTRACK> depth %s -> backtrack to state %s',depth ,current_state.get_id() )
        self.crawler.executor_backtrack(current_state, self.executor)
        logging.info('==========< BACKTRACK END   >==========')

    def update_with_new_state(self, current_state, new_state, new_edge, action, depth, dom_list, url):
        # automata save new state 
        logging.info(' |depth:%s state:%s| add new state %s of : %s', depth, current_state.get_id(), new_state.get_id(), url )

        self.automata.save_state(self.executor, new_state, depth)
        self.automata.save_state_shot(self.executor, new_state)

        if depth < self.configuration.get_max_depth():
            self.crawler.add_new_events(new_state, current_state, depth)

    def update_with_old_state(self, current_state, new_state, new_edge, action, depth, dom_list, url):
        #check if old state have a shorter depth
        if depth < new_state.get_depth():
            new_state.set_depth(depth)
            self.crawler.add_new_events(new_state, current_state, depth)

    def save_traces(self):
        self.automata.save_simple_traces()

    def end(self):
        pass

class MonkeyCrawler(AlgoCrawler):
    def __init__(self):
        self.trace_length_count = 0
        self.traces = []
        self.trace_history = {}

    def set_utility(self, crawler, configuration, executor, automata):
        self.crawler = crawler
        self.configuration = configuration
        self.executor = executor
        self.automata = automata

    def prepare(self):
        #executor
        self.executor.start()
        self.executor.goto_url()
        #initial state
        initial_state = self.crawler.get_initail_state()
        #save trace
        self.trace_length_count = 0
        self.trace_history = { 'states': [ initial_state ], 'edges': [] }

        self.crawler.run_script_before_crawl(initial_state)

    def add_new_events(self, state, prev_state, depth):
        candidate_clickables = []

        for clickables, iframe_key in DomAnalyzer.get_clickables(state, prev_state if prev_state else None):
            for clickable in clickables:
                candidate_clickables.append( (clickable, iframe_key) )
        if not candidate_clickables:
            return

        clickable, iframe_key = random.choice( candidate_clickables )
        self.crawler.action_events.append( {
            'state'  : state,
            'action' : { 'clickable':clickable, 'iframe_key':iframe_key },
            'depth'  : depth,
        } )
        print(state.get_id(),clickable.get_id(), clickable.get_xpath())
        
    def get_next_action(self, action_events):
        event = action_events.pop()
        return event

    def change_state(self, state, action, depth):
        #logging.info('==========< BACKTRACK START >==========')
        #logging.info('==<BACKTRACK> depth %s -> backtrack to state %s',depth ,state.get_id() )
        #self.crawler.executor_backtrack(state, self.executor)
        #logging.info('==========< BACKTRACK END   >==========')
        logging.info('==========< MONKEY IGNORE BACKTRACK  >==========')

    def trigger_action(self, state, new_edge, action, depth):
        logging.info(' |depth:%s state:%s| fire element in iframe(%s)', depth, state.get_id(), action['iframe_key'])
        self.trace_length_count += 1

        self.crawler.make_value(new_edge)
        self.executor.click_event_by_edge(new_edge)

    def update_with_same_state(self, current_state, new_edge, action, depth, dom_list, url):
        #save trace
        self.trace_history['states'].append(current_state)
        self.trace_history['edges'].append(new_edge)
        #get new event again
        if self.trace_length_count < self.configuration.get_max_length():
            self.crawler.add_new_events(current_state, None, depth)

    def update_with_out_of_domain(self, current_state, new_edge, action, depth, dom_list, url):
        # back if state out of domain
        logging.info(' |depth:%s state:%s| out of domain: %s', depth, current_state.get_id(), url)
        logging.info('==========< BACKTRACK START >==========')
        logging.info('==<BACKTRACK> depth %s -> backtrack to state %s',depth ,current_state.get_id() )
        self.crawler.executor_backtrack(current_state, self.executor)
        logging.info('==========< BACKTRACK END   >==========')

        #get new event again
        if self.trace_length_count < self.configuration.get_max_length():
            self.crawler.add_new_events(current_state, None, depth)

    def update_with_new_state(self, current_state, new_state, new_edge, action, depth, dom_list, url):
        #save trace
        self.trace_history['states'].append(new_state)
        self.trace_history['edges'].append(new_edge)
        # automata save new state 
        logging.info(' |depth:%s state:%s| add new state %s of : %s', depth, current_state.get_id(), new_state.get_id(), url )
        self.automata.save_state(self.executor, new_state, depth)
        self.automata.save_state_shot(self.executor, new_state)

        if self.trace_length_count < self.configuration.get_max_length():
            self.crawler.add_new_events(new_state, None, depth)

    def update_with_old_state(self, current_state, new_state, new_edge, action, depth, dom_list, url):
        #save trace
        self.trace_history['states'].append(new_state)
        self.trace_history['edges'].append(new_edge)
        #check if old state have a shorter depth
        if depth < new_state.get_depth():
            new_state.set_depth(depth)
        if depth > new_state.get_depth():
            depth = new_state.get_depth()
        
        if self.trace_length_count < self.configuration.get_max_length():
            self.crawler.add_new_events(new_state, None, depth)

    def save_traces(self):
        self.automata.save_traces(self.traces)

    def end(self):
        self.traces.append( self.trace_history )
        self.trace_length_count = 0
        self.trace_history = {}

class CBTMonkeyCrawler(AlgoCrawler):
    def __init__(self):
        self.trace_length_count = 0
        self.traces = []
        self.trace_history = {}
        self.other_executor = None

    def add_executor(self, argv):
        self.other_executor = SeleniumExecutor(browserID, config.get_url())

    def set_utility(self, crawler, configuration, executor, automata):
        self.crawler = crawler
        self.configuration = configuration
        self.executor = executor
        self.automata = automata

    def prepare(self):
        #executor
        self.executor.start()
        self.executor.goto_url()

        self.other_executor.start()
        self.other_executor.goto_url()
        #initial state
        initial_state = self.crawler.get_initail_state()
        #save trace
        self.trace_length_count = 0
        self.trace_history = { 'states': [ initial_state ], 'edges': [] }

        self.crawler.run_script_before_crawl(initial_state)

    def add_new_events(self, state, prev_state, depth):
        candidate_clickables = []

        for clickables, iframe_key in DomAnalyzer.get_clickables(state, prev_state if prev_state else None):
            for clickable in clickables:
                candidate_clickables.append( (clickable, iframe_key) )

        if not candidate_clickables:
            return

        clickable, iframe_key = random.choice( candidate_clickables )
        print(state.get_id(),clickable.get_id(), clickable.get_xpath())
        self.crawler.action_events.append( {
            'state'  : state,
            'action' : { 'clickable':clickable, 'iframe_key':iframe_key },
            'depth'  : depth,
        } )
        
    def get_next_action(self, action_events):
        event = action_events.pop()
        return event

    def change_state(self, state, action, depth):
        logging.info('==========< BACKTRACK START >==========')
        logging.info('==<BACKTRACK> depth %s -> backtrack to state %s',depth ,state.get_id() )
        self.crawler.executor_backtrack(state, self.executor, self.other_executor)
        logging.info('==========< BACKTRACK END   >==========')

    def trigger_action(self, state, new_edge, action, depth):
        logging.info(' |depth:%s state:%s| fire element in iframe(%s)', depth, state.get_id(), action['iframe_key'])
        self.trace_length_count += 1

        self.crawler.make_value(new_edge)
        self.executor.click_event_by_edge(new_edge)
        self.other_executor.click_event_by_edge(new_edge)

    def update_with_same_state(self, current_state, new_edge, action, depth, dom_list, url):
        #save trace
        self.trace_history['states'].append(current_state)
        self.trace_history['edges'].append(new_edge)
        #get new event again
        if self.trace_length_count < self.configuration.get_max_length():
            self.crawler.add_new_events(current_state, None, depth)

    def update_with_out_of_domain(self, current_state, new_edge, action, depth, dom_list, url):
        #save trace
        self.trace_history['states'].append(current_state)
        self.trace_history['edges'].append(new_edge)
        # back if state out of domain
        logging.info(' |depth:%s state:%s| out of domain: %s', depth, current_state.get_id(), url)
        logging.info('==========< BACKTRACK START >==========')
        logging.info('==<BACKTRACK> depth %s -> backtrack to state %s',depth ,current_state.get_id() )
        self.crawler.executor_backtrack(current_state, self.executor, self.other_executor)
        logging.info('==========< BACKTRACK END   >==========')

        #get new event again
        if self.trace_length_count < self.configuration.get_max_length():
            self.crawler.add_new_events(current_state, None, depth)

    def update_with_new_state(self, current_state, new_state, new_edge, action, depth, dom_list, url):
        #save trace
        self.trace_history['states'].append(new_state)
        self.trace_history['edges'].append(new_edge)
        # automata save new state 
        logging.info(' |depth:%s state:%s| add new state %s of : %s', depth, current_state.get_id(), new_state.get_id(), url )
        self.automata.save_state(self.executor, new_state, depth)
        self.automata.save_state_shot(self.executor, new_state)

        self.check_diff_browser()


        if self.trace_length_count < self.configuration.get_max_length():
            self.crawler.add_new_events(new_state, None, depth)

    def update_with_old_state(self, current_state, new_state, new_edge, action, depth, dom_list, url):
        #save trace
        self.trace_history['states'].append(new_state)
        self.trace_history['edges'].append(new_edge)
        #check if old state have a shorter depth
        if depth < new_state.get_depth():
            new_state.set_depth(depth)
        if depth > new_state.get_depth():
            depth = new_state.get_depth()
        
        if self.trace_length_count < self.configuration.get_max_length():
            self.crawler.add_new_events(new_state, None, depth)

    def save_traces(self):
        self.automata.save_traces(self.traces)

    def end(self):
        self.traces.append( self.trace_history )
        self.trace_length_count = 0
        self.trace_history = {}
        self.other_executor.close()

    def check_diff_browser(self):
        # 1. check executor other_executor is same state

        # 2. if same , analsis 
        analysis_elements( self.executor )
        analysis_elements( self.other_executor )

        analysis_with_other_browser()

    def analysis_elements(self, executor):
        pass

    def analysis_with_other_browser(self):
        pass