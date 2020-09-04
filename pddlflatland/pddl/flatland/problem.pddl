;flatland-problem.pddl 2020-08-30 @xplanlab

;input objects: railway, cell, agent

;input initial:
;   1. weight, height of railway
;   2. position, transition, available or not  of each cell in railway
;   3. direction, position of each agent
;   4. other status of each agent, like "moving","status"

;input goal: target position of each agent

(define 
    (problem task01) 
    (:domain flatland)
    (:objects
        rail - railway

	    c00 - cell 
        c01 - cell 
        c02 - cell 
        c10 - cell 
        c11 - cell 
        c12 - cell  
        c20 - cell 
        c21 - cell
        c22 - cell 
        
        agent0 - agent 
        agent1 - agent 
    )
    (:init
        (= (height rail) 3)
        (= (weight rail) 3)

        (= (direction agent0) 0)
        (= (direction agent1) 2)
        (at agent0 c11)
        (at agent1 c02)

        (= (position c00) 1)
        (= (position c01) 2)
        (= (position c02) 3)
        (= (position c10) 4)
        (= (position c11) 5)
        (= (position c12) 6)
        (= (position c20) 7)
        (= (position c21) 8)
        (= (position c22) 9)

        (= (transition c00) 2)
        (= (transition c01) 2)
        (= (transition c02) 1)
        (= (transition c10) 1)
        (= (transition c11) 7)
        (= (transition c12) 1)
        (= (transition c20) 1)
        (= (transition c21) 2)
        (= (transition c22) 11)

        (available c01)
        (available c10)
        (available c00)
        (available c12)
        (available c20)
        (available c21)
        (available c22)
       
    )
    (:goal (and
		(at agent0 c00)
        (at agent1 c20))
    )
)
