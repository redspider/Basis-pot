# Basis concepts

## Technology stack

### Request service: Pyramid

Pyramid represents the latest and arguably best python web application foundation, for the purposes of being modified to fit our needs.

While other frameworks such as Django offer a codebase that has been stable for longer, modifying it to match the remainder of the requirements would
involve significantly more work and lead us even further from the core.

### RDBMS: PostgreSQL

By far the leading open source RDBMS, PostgreSQL offers the primary advantages of both powerful constructs (WINDOW functions etc), and
highly reliable constraints and transactions. There are no real non-commercial competitors in this area.

Addressing MySQL, it is fair to say any number of single missing features makes it unsuitable for our purposes, however
the simplest case is that:

```
CREATE TABLE foo (
    bar INT NOT NULL
);

INSERT INTO foo (bar) VALUES (NULL);
```

Does not raise an exception or otherwise fail to complete the commit, it simply converts the NULL into 0. This is so
mind-bogglingly incorrect as to leave me terrified about what other bizarre things it might do with my data.

### NoSQL store: MongoDB

Each of the NoSQL systems has significant overlap with the others, and some level of specialisation. Most of them are
pretty good and could reasonably be used for our purposes. MongoDB is chosen due partly to familiarity, and partly
because it isn't a key/value store and thus supports a couple of additional query modes that are useful for us.

Redis is the strongest competitor for this position and would probably be equally capable, with the caveat that it
is more about k/v storage. One possible reason why we may change this decision is that Redis offers PUB/SUB and queue
operators that could plausibly be used to remove the need for 0MQ.

### Messaging: 0MQ

A tightly contested position, the backend communications loop was a close tie between Redis, 0MQ and RabbitMQ. Indeed
Rabbit had been decided upon, but discussion with someone who had been using most of the solutions in production
convinced me to switch to 0MQ. The fundamental issue is that Rabbit represents a complex solution, and it becomes
difficult to diagnose in the event of weird failure, which apparently is just not all that uncommon (it's not Rabbit itself,
 various drivers, reconnect sequences etc can apparently cause problems).

0MQ on the other hand is simple and meets our need for non-reliable messaging that does not block. In addition, it is
possible to create relay nodes that allow us to implement the various message patterns we may require without hoping that
Rabbit provides them.

### Evented browser communications: NodeJS

Jumping the last mile to communicate in realtime back to the browser is tricky. A number of mature concepts such as long-poll
perform this task in a rather inefficient way, but reliable support for these has proven to be fairly limited. Our
 options were reduced to Socket.IO, Orbited and nginx http-longpoll.

Of these, orbited was rejected because it does not support the particular addressing mode we wanted, and http-longpoll
was rejected after checking with others indicated it was both unmaintained and had a memory leak that necessitated restarts
of the nginx process after some time. Socket.IO therefore was more of a win-by-default than because it was an outstanding
option.

Prior experience has demonstrated that there is only one reliable Socket.IO server implementation, the one in Node.JS.
Others, such as the various python endpoints, had odd corner-case bugs that led to problems in production use. As a
result the last mile will be served by a low-complexity Node.JS instance accepting messages for 0MQ.

### CSS construction: Open position

Contenders SCSS with Compass, vs LessCSS

### Javascript state: Open position

Contenders: Backbone, SammyJS, Custom

### Front-end web connection management: nginx

nginx remains our preferred option as the front-end connection handler. Alternatives could plausibly be varnish
or lighthttp but neither offer compelling features we don't already have.





