#!/usr/bin/env racket
#lang racket/gui
(require racket/gui/base)
(require racket/tcp)

;;; Server Stuff
; Connect to first bot
(display "Waiting for First Bot Connection\n")
(define listener (tcp-listen 8085 2 #t "127.0.0.1"))
(define-values (in1 out1) (tcp-accept listener))
(define name1 (read in1))
(flush-output out1)
(display (format "~a connected\n" name1))

; Connect to second bot
(display "Waiting for Second Bot Connection\n")
(define-values (in2 out2) (tcp-accept listener))
(define name2 (read in2))
(flush-output out2)
(display (format "~a connected" name2))

(define (send-command command coord destination)
  (define output (format "~a/~a, ~a" command (first coord) (second coord)))
  (write output destination)
  (flush-output destination))


;;; Game
(define size 19)

(define (new-board)
  (build-vector size (lambda (row) (make-vector size 1))))

(define board (new-board))
(define last-added empty)
(define turn 2)
(define winner #f)
(define ai-turn #f)

(define (board-get row col)
  (vector-ref (vector-ref board row) col))

(define (board-set row col val)
  (vector-set! (vector-ref board row) col val))

(define (add-piece row col)
  (define added #f)
  (when (and (<= 0 row 18) (<= 0 col 18) (eq? (board-get row col) 1))
    (board-set row col turn)
    (set! last-added (cons row col))
    (set! turn (if (eq? turn 2) 0 2))
    (set! added #t))
  added)

(define (check-winner)
  (define-values (row col) (values (car last-added) (cdr last-added)))
  (define player (board-get row col))

  (define (neighbors change-x change-y dir)
    (for*/fold ((neighbors empty) (reached-end #f) #:result neighbors)
               ((i (in-range 1 5)))
      (define-values (x y) (values (+ row (* dir (* i change-y)))
                                   (+ col (* dir (* i change-x)))))
      (cond ((and (not reached-end) (<= 0 x 18) (<= 0 y 18) (= player (board-get x y)))
             (values (cons (list x y) neighbors) #f))
            (else (values neighbors #t)))))

  (for*/or ((x '((1 . 0) (0 . 1) (1 . 1) (-1 . 1))))
    (define pieces (append (neighbors (car x) (cdr x) 1)
                           (neighbors (car x) (cdr x) -1)))
    (and (<= 4 (length pieces))
         (set! winner (list player (cons (list row col) pieces))))))

(define (new-game game-type)
  (set! board (new-board))
  (set! last-added empty)
  (set! turn 2)
  (set! winner #f)
  (send-command "new_game" (list 0 0) out1)
  (send-command "new_game" (list 0 0) out2)
  (when (= game-type 3) (thread (lambda () (ai-vs-ai 0 name1 name2))))
  (when (= game-type 4) (thread (lambda () (ai-vs-ai 0 name2 name1)))))

(define (ai-vs-ai turn_cnt first_bot second_bot)
  ; recursive turn function, runs until a valid turn is made
  (set! ai-turn #t)
  (define (turn bot_in bot_out)
    (define command (if (= turn_cnt 0) "start" "turn"))
    (define point (if (= turn_cnt 0) (list 0 0) (list (car last-added) (cdr last-added))))
    (send-command command point bot_out)
    (define choice (read bot_in))
    (when (not (add-piece (first choice) (second choice)))
      (turn bot_in bot_out #f)))
  
  ; define which bot is black and which is white
  (define-values (b_in b_out w_in w_out)
    (if (equal? first_bot name1)
        (values in1 out1 in2 out2)
        (values in2 out2 in1 out1)))
  
  ; apply a turn
  (when (not winner)
    (if (even? turn_cnt)
        (turn b_in b_out)
        (turn w_in w_out))
    (send canvas manual-update-pieces)
    (ai-vs-ai (add1 turn_cnt) first_bot second_bot))
  (set! ai-turn #t))


;;; Gui
(define bg-image (make-object bitmap% "kaya_4k.jpg"))
(define font (send the-font-list find-or-create-font 20 'default 'normal 'bold))
(define no-brush (make-object brush% "black" 'transparent))
(define red-pen (make-object pen% "red" 5 'solid))
(define black-pen (make-object pen% "black" 5 'solid))
(define white-pen (make-object pen% "white" 5 'solid))
(define black-brush (make-object brush% "black" 'solid))
(define white-brush (make-object brush% "white" 'solid))

(define (calc-widths-and-heights dc)
  (define-values (total-w total-h) (send dc get-size))
  (define-values (margin-w margin-h) (values (/ total-w 20) (/ total-h 20)))
  (define-values (grid-w grid-h) (values (- total-w (* margin-w 2)) (- total-h (* margin-h 2))))
  (define-values (cell-w cell-h) (values (/ grid-w (sub1 size)) (/ grid-h (sub1 size))))
  (values margin-w margin-h cell-w cell-h))

(define (nearest-intersection mouse-x mouse-y dc)
  (define (dist x1 y1 x2 y2) (sqrt (+ (expt (- x2 x1) 2) (expt (- y2 y1) 2))))
  (define-values (margin-w margin-h cell-w cell-h) (calc-widths-and-heights dc))
  (for*/fold ((nearest (list 0 0 +inf.0)))
             ((row (in-range size)) (col (in-range size)))
    (define-values (x y) (values (+ (* col cell-w) margin-w) (+ (* row cell-h) margin-h)))
    (define distance (dist mouse-x mouse-y x y))
    (values (if (> (last nearest) distance) (list row col distance) nearest))))

(define (draw-goban dc)
  (define-values (margin-w margin-h cell-w cell-h) (calc-widths-and-heights dc))
  (send dc draw-bitmap bg-image 0 0)
  (send dc set-pen black-pen)
  (send dc set-brush no-brush)
  ;; draw the grid
  (for* ((row (in-range (sub1 size))) (col (in-range (sub1 size))))
    (define-values (x y) (values (+ (* col cell-w) margin-w) (+ (* row cell-h) margin-h)))
    (send dc draw-rectangle x y cell-w cell-h))

  ;; draw the row labels
  (define (string-range start end)
    (for/list ((x (in-inclusive-range start end))) `(,@(~v x))))

  (for (((col index) (in-indexed (string-range 1 size))))
    (define-values (_0 h _1 _2) (send dc get-text-extent col font #t))
    (define y (+ (* index cell-h) (- cell-h (/ h 3.5))))
    (send dc draw-text col 3 y))

  ;; draw the column labels
  (for (((row index) (in-indexed (string->list "ABCDEFGHIJKLMNOPQRS"))))
    (define-values (w _0 _1 _2) (send dc get-text-extent (string row) font #t))
    (define x (+ (* index cell-w) (- cell-w (/ w 3.5))))
    (send dc draw-text (string row) x 3)))

(define (draw-pieces dc)
  (define-values (margin-w margin-h cell-w cell-h) (calc-widths-and-heights dc))
  (define-values (piece-w piece-h) (values (/ cell-w 1.12) (/ cell-h 1.12)))
  (send dc set-pen white-pen)
  (send dc set-brush white-brush)

  ; draw pieces
  (for* ((row (in-range size)) (col (in-range size)))
    (define-values (x y) (values (- (+ (* col cell-w) margin-w) (/ piece-w 2))
                                 (- (+ (* row cell-h) margin-h) (/ piece-h 2))))
    (define player (board-get row col))
    (when (not (eq? player 1))
      (send dc set-pen (if (eq? player 2) black-pen white-pen))
      (send dc set-brush (if (eq? player 2) black-brush white-brush))
      (send dc draw-ellipse x y piece-w piece-h)
      ; draw marker for the last piece placed
      (when (equal? (cons row col) last-added)
        (define-values (marker-w marker-h) (values (/ piece-w 2.5) (/ piece-h 2.5)))
        (send dc set-pen (if (eq? player 2) white-pen black-pen))
        (send dc set-brush no-brush)
        (send dc draw-ellipse
              (+ (- (/ piece-w 2) (/ marker-w 2)) x)
              (+ (- (/ piece-h 2) (/ marker-h 2)) y)
              marker-w marker-h)))))

(define (draw-win-line dc)
  (define-values (margin-w margin-h cell-w cell-h) (calc-widths-and-heights dc))
  (send dc set-pen red-pen)
  (define points
    (map (lambda (p)
           (cons (+ (* (cadr p) cell-w) margin-w) (+ (* (car p) cell-h) margin-h)))
         (cadr winner)))
  (send dc draw-lines points))
  
(define frame
  (new frame%
       (label "Gomoku")
       (width 700)
       (height 700)))

(define my-canvas%
  (class canvas%
    (define/override (on-event event)
      (unless ai-turn
        (define-values (mouse-x mouse-y) (values (send event get-x) (send event get-y)))
        (define e-type (send event get-event-type))
        (define dc (send this get-dc))
        (when (and (not winner) (or (eq? e-type 'left-down) (eq? e-type 'right-down)))
          (define point (nearest-intersection mouse-x mouse-y dc))
          (add-piece (first point) (second point))
          (check-winner)
          (draw-pieces dc)
          (when winner (draw-win-line dc))
          (send-command "turn" point out1)
          (send-command "turn" point out2))))
    (define/public (manual-update-pieces)
      (define dc (send this get-dc))
      (draw-pieces dc)
      (check-winner)
      (when winner (draw-win-line dc)))
    (super-new)))

(define canvas 
  (new my-canvas% 
       (parent frame)
       (min-width 600)
       (min-height 600)
       (paint-callback
        (lambda (canvas dc)
          (draw-goban dc)
          (draw-pieces dc)
          (when winner (draw-win-line dc))))))

(define menu-bar
  (new menu-bar%
    (parent frame)))
(define game-menu
  (new menu%
    (label "&Game")
    (parent menu-bar)))
(define new-game-menu
  (new menu%
       (label "&New Game")
       (parent game-menu)))
(define ai-vs-ai-menu
  (new menu%
       (label "&Ai vs Ai")
       (parent new-game-menu)))
(define settings-menu
  (new menu%
    (label "&Settings")
    (parent menu-bar)))

(new menu-item%
  (label "&Exit")
  (parent game-menu)
  (callback (λ (m event)
              (send-command "close" (list 0 0) out1)
              (send-command "close" (list 0 0) out2)
              (close-input-port in1)
              (close-input-port in2)
              (close-output-port out1)
              (close-output-port out2)
              (tcp-close listener)
              (exit '()))))

(new menu-item%
     (label "Play &First")
     (parent new-game-menu)
     (callback (lambda (m event)
                 (set! winner (list #t empty))
                 (new-game 1)
                 (send canvas refresh))))
(new menu-item%
     (label "Play &Second")
     (parent new-game-menu)
     (callback (lambda (m event)
                 (set! winner (list #t empty))
                 (new-game 2)
                 (send canvas refresh))))
(new menu-item%
     (label (format "&B: ~a, W: ~a" name1 name2))
     (parent ai-vs-ai-menu)
     (callback (lambda (m event)
                 (set! winner (list #t empty))
                 (new-game 3)
                 (send canvas refresh))))

(new menu-item%
     (label (format "&B: ~a, W: ~a" name2 name1))
     (parent ai-vs-ai-menu)
     (callback (lambda (m event)
                 (set! winner (list #t empty))
                 (new-game 4)
                 (send canvas refresh))))

(send frame show #t)
