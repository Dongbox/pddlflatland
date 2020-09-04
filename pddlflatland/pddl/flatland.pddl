;flatland-domain.pddl 2020-08-30 @xplanlab
(define 
    (domain flatland)
    (:requirements :typing :numeric-fluents)
    (:types agent cell railway)
    (:predicates 
	    (at ?v0 - agent ?v1 - cell)
	    (available ?v0 - cell)
		(moving ?x - agent)
    )

	;height,weight for railway
	;position of cell : (x*y)
	;direction of agent : 0,1,2,3 for north,east,south,west
	;status of agent : 0,1,2,3 for ready,active,done,done removed
	;transition of cell : 	N	E	S	W	(exit) (example)
	;	(enter)		N		0	0	0	1				
	;				E		0	1	1	0
	;				S		0	0	0	0	
	;				W		0	0	0	1

	(:functions
		(height ?x - railway)
		(weight ?x - railway)
		(position ?x - cell)
		(direction ?x - agent)
		(transition ?x - cell)
		(status ?x - agent)
	)

	;action : move-left, move-right, move-forward, stop
	(:action move-left
		:parameters (?r - railway ?x - agent ?c - cell ?c2 - cell)
		:precondition (and 
			(or 
				(and (= (direction ?x) 1) (= (transition ?c) 8) (= (-(position ?c) (position ?c2)) (weight ?r))
				)
				(and (= (direction ?x) 2) (= (transition ?c) 9) (= (-(position ?c2) (position ?c)) 1)
				)
				(and (= (direction ?x) 3) (= (transition ?c) 10) (= (-(position ?c2) (position ?c)) (weight ?r)) 				
				)
				(and (= (direction ?x) 0) (= (transition ?c) 7) (= (-(position ?c) (position ?c2)) 1) 
				)
			)
			(available ?c2)
			(at ?x ?c)
        )
		:effect (and
			(available ?c)
			(at ?x ?c2)
			(not (available ?c2))
			(when (= (direction ?x) 1) (assign (direction ?x) 0))
			(when (= (direction ?x) 2) (assign (direction ?x) 1))
			(when (= (direction ?x) 3) (assign (direction ?x) 2))
			(when (= (direction ?x) 0) (assign (direction ?x) 3))
		)
	)

	(:action move-right
		:parameters (?r - railway ?x - agent ?c - cell ?c2 - cell)
		:precondition (and 
			(or 
				(and (= (direction ?x) 1) (= (transition ?c) 12) (= (-(position ?c2) (position ?c)) (weight ?r))
				)
				(and (= (direction ?x) 2) (= (transition ?c) 11) (= (-(position ?c) (position ?c2)) 1)
				)
				(and (= (direction ?x) 3) (= (transition ?c) 14) (= (-(position ?c) (position ?c2)) (weight ?r))
				)
				(and (= (direction ?x) 0) (= (transition ?c) 13) (= (-(position ?c2) (position ?c)) 1)
				)
			)
			(available ?c2)
			(at ?x ?c)
        )
		:effect (and
			(available ?c)
			(at ?x ?c2)
			(not (available ?c2))
			(when (= (direction ?x) 1) (assign (direction ?x) 2))
			(when (= (direction ?x) 2) (assign (direction ?x) 3))
			(when (= (direction ?x) 3) (assign (direction ?x) 0))
			(when (= (direction ?x) 0) (assign (direction ?x) 1))
			)
	)

	(:action move-forward
		:parameters (?r - railway ?x - agent ?c - cell ?c2 - cell)
		:precondition (and 
			(or 
				(and (= (direction ?x) 1) (= (transition ?c) 2) (= (-(position ?c2) (position ?c)) 1) 
				)
				(and (= (direction ?x) 2) (= (transition ?c) 1) (= (-(position ?c2) (position ?c)) (weight ?r))
				)
				(and (= (direction ?x) 3) (= (transition ?c) 2) (= (-(position ?c) (position ?c2)) 1)
				)
				(and (= (direction ?x) 0) (= (transition ?c) 1) (= (-(position ?c) (position ?c2)) (weight ?r))
				)
			) 
			(available ?c2)
			(at ?x ?c)
        )
		:effect (and
			(available ?c)
			(at ?x ?c2)
			(not (available ?c2))
			(when (= (direction ?x) 1) (assign (direction ?x) 1))
			(when (= (direction ?x) 2) (assign (direction ?x) 2))
			(when (= (direction ?x) 3) (assign (direction ?x) 3))
			(when (= (direction ?x) 0) (assign (direction ?x) 0))
			)
	)

	(:action stop
		:parameters (?x -agent ?c - cell)
		:precondition (and 
		(at ?x ?c)
		(moving ?x)
		)
		:effect (and 
		(at ?x ?c)
		(not (moving ?x))
		)
	)
	
)
        