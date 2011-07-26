# Basis concepts

## Technology stack

### Request service: Pyramid

[Pyramid](http://pylonsproject.org/) represents the latest and arguably best python web application foundation, for the purposes of being modified to fit our needs.

While other frameworks such as [Django](https://www.djangoproject.com/) offer a code base that has been stable for longer, modifying it to match the remainder of the requirements would
involve significantly more work and lead us even further from the core.

### RDBMS: PostgreSQL

By far the leading open source RDBMS, [PostgreSQL](http://www.postgresql.org/) offers the primary advantages of both powerful constructs (WINDOW functions etc), and
highly reliable constraints and transactions. There are no real non-commercial competitors in this area.

Addressing MySQL, it is fair to say any number of single missing features makes it unsuitable for our purposes.

### NoSQL store: MongoDB

A NoSQL store is used for storing a variety of data that isn't easily or usefully stored in the RDBMS. A good example
of this is the event log, that stores an arbitrary dictionary supplied by the application on a case-by-case basis. In
the event that the log data is lost, well..it's not that big a deal.

Each of the NoSQL systems has significant overlap with the others, and some level of specialisation. Most of them are
pretty good and could reasonably be used for our purposes. [MongoDB](http://www.mongodb.org/) is chosen due partly to familiarity, and partly
because it isn't a key/value store and thus supports a couple of additional query modes that are useful for us.

[Redis](http://redis.io/) is the strongest competitor for this position and would probably be equally capable, with the caveat that it
is more about k/v storage. One possible reason why we may change this decision is that Redis offers PUB/SUB and queue
operators that could plausibly be used to remove the need for 0MQ.

### Messaging: 0MQ

A tightly contested position, the backend communications loop was a close tie between Redis, [0MQ](http://www.zeromq.org/) and [RabbitMQ](http://www.rabbitmq.com/). Indeed
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
 options were reduced to [Socket.IO](http://socket.io/), [Orbited](http://www.orbited.org/) and [nginx http-push](http://pushmodule.slact.net/).

Of these, orbited was rejected because it does not support the particular addressing mode we wanted, and http-push
was rejected after checking with others indicated it was both unmaintained and had a memory leak that necessitated restarts
of the nginx process after some time. Socket.IO therefore was more of a win-by-default than because it was an outstanding
option.

Prior experience has demonstrated that there is only one reliable Socket.IO server implementation, the one in [Node.JS](http://nodejs.org/).
Others, such as the various python endpoints, had odd corner-case bugs that led to problems in production use. As a
result the last mile will be served by a low-complexity Node.JS instance accepting messages for 0MQ.

### CSS construction: Open position

Contenders [SASS](http://sass-lang.com/) with [Compass](http://compass-style.org/), vs [LessCSS](http://lesscss.org/)

### Javascript libraries: [jQuery](http://jquery.com/), [Sugar](http://sugarjs.com/), possibly [TameJS](http://tamejs.org/)

Not sold on TameJS yet. Breaking the exception mechanisms and generally making tracebacks harder to understand is not
a laudable goal. That said, it does help deal with ZOMGCALLBACKS.

### Javascript state: Open position

Contenders: [Backbone](http://documentcloud.github.com/backbone/), [SammyJS](http://sammyjs.org/), Custom

### UI Assist

* [Chosen](http://harvesthq.github.com/chosen/) provides handy select improvements
* [Formalize](http://formalize.me/) provides a normalised form environment
* [Flexie](https://github.com/doctyper/flexie#readme) patches box support into non-box browsers
* [HeadJS](http://headjs.com/) javascript loader and some basic modernizer/detection support

### Graphics/Charting

Options include:

* [d3.js](http://mbostock.github.com/d3/)
* [processingjs](http://processingjs.org/)

### Front-end web connection management: nginx

[nginx](http://nginx.org/en/) remains our preferred option as the front-end connection handler. Alternatives could plausibly be [varnish](https://www.varnish-cache.org/)
or [lighttpd](http://www.lighttpd.net/) but neither offer compelling features we don't already have.

### Testing: Open position

Heavy javascript component makes this tricky.

## Modifications to Pyramid

As yet it has not been necessary to modify pyramid itself, although that may yet come given the need to capture traceback
information in the event of an error. The following non-standard components have been introduced:

### Modified Model

Our code cleanly separates the Model from the storage structure. The task of enforcing business rules and managing data
storage and transmission is built into the Model itself and is completely opaque to the Views.

The following reasons back up this choice:

#### Clear communication of intent

A method entitled user.get() does a poor job of communicating its purpose. How much of the user information should it
retrieve? As a result we focus on creating a Model interface that communicates intent to the backend to allow it to
make smart decisions. An example of this may be:

```
user.get_for_session(account)
```

Which allows the Model to then retrieve precisely the fields required for the purposes of being in a session, as well
as take optimisations if it can.

#### Storage-agnostic

The exact structure of the database has no impact on anything outside the Model. This allows for testing of the Model
interface only, in order to guarantee that design changes to the schema (such as the introduction of views or partitioning
tables) don't affect the rest of the app.

#### Multi-storage capable

RDBMS and NoSQL each have different, somewhat overlapping strengths. By refusing to tie the Model to the structure of
any one data store, we are free to make use of both concepts as appropriate, storing non-critical, flexible data
 within MongoDB while keeping critical information within the reliable PostgreSQL store.

In addition it allows the model to handle files, and send messages, in an intuitive way even when no interaction with
a store is necessary.

### Identity session / authentication

While Pyramid offers its own Session and Authentication systems, we have chosen to implement our own. Ours offers a small
number of moderate benefits, primarily focused on security. This is not to imply that the existing pyramid offerings are
insecure, merely that ours attempts to follow the [OWASP guidelines](https://www.owasp.org/index.php/Session_Management) more closely. Our session is more properly titled an
"Identity Session". It is not designed for temporary storage of data, but for session-length storage of identity
credentials.

In addition, the storage-tied nature of our implementation allows us to avoid some complexity.

#### Group expiry

Our sessions can be expired as a group based on the owning user, allowing an action such as changing a password to
 force-logout an attacker who may have obtained a different session.

#### Permissions boundaries

Our sessions can be rotated when crossing permissions boundaries (sign-in, administrative access), preventing pre-auth
compromises of the session token from carrying forward.

#### One-time, keyed CSRF tokens

CSRF tokens in our implementation cannot be re-used (replay attack) nor can they be used in a submission other than
the one for which they were generated (keys). It is not clear the replay prevention brings any actual benefits.

#### Actor

Our implementation explicitly differentiates between the real user, and the actor. This allows the vast majority of the
codebase to act as if the actor is the only user that matters, and admins can transition between themselves and any
other user on the system in order to perform investigations or support.

### Event log

Again a benefit of having a guaranteed NoSQL store available, the event log system allows us to record everything, in
great detail, to MongoDB for trend tracking, alerting, and realtime delivery to admin clients. The event log offers
both the standard warn()/debug() etc as well as automatically storing the request and response headers of every request.

The event log accepts a dictionary, not a string, and the dictionary is pushed all the way through to MongoDB, allowing
for smart queries against, for example, a given session ID.

### Validation

With the general understanding that validation is to occur client-side, validation for this system becomes a simpler
(and therefore more secure) operation. There is no need to feed back precisely what went wrong, only to fail to
accept invalid data. The validate lib begins this process by introducing wrapper functions that pass the data through
if it is acceptable, or raise an exception otherwise.

This mode of expression:

```
username = validate.username(request.POST['username'])
```

Makes it easy to visually spot incoming data that has not yet been validated. Some consideration has been given to
improving this interface to act like this:

```
username = request.post('username',v.username)
```

thus ensuring that no inputs will be accepted without specifying a validator.

Validation functions are designed to operate in a multi-layer manner relying on non-type-specific operations first if
possible, i.e. an incoming number is checked using a regular expression first, before checking with the int() function
in order to isolate possible bugs in the underlying python implementation of re or int(). There are limits to how well
this can be done without being silly, but we try.

## Systems, management

### System configuration

[Puppet](http://www.puppetlabs.com/). [Chef](http://wiki.opscode.com/display/chef/Home) is the other option but we already have rulesets for puppet so we'll stick with that.

### System Monitoring

[ServerDensity](http://www.serverdensity.com/) at this point, possibly with [Pingdom](http://www.pingdom.com/) for simple uptime presence. Not a lot of visibility into good alternatives. ServerDensity is particularly weak on PostgreSQL monitoring which is a shame, strong on MongoDB though.

### System log tracking

System logs will be fed into [Loggly](http://loggly.com/). While Loggly, [Papertrail](https://papertrailapp.com/) etc are nice, none
of them have matured sufficiently to truly build intelligence out of the logs (unlike, say, [Splunk](http://www.splunk.com/), which simply has abysmal
licensing). Log analysis at the system level isn't that common at this point however.

### Application log tracking

Custom work built on top of MongoDB/0MQ. The existing offerings such as [Errormator](https://errormator.com/) offer a more robust product than we
will be able to produce initially given other priorities, however the sheer volume of data we intend to track and the
need to deal with analysis of it rather than simply identifying and tracking exceptions does not appear to be served
by anyone at this time.

## Services

### Hosting provider

[Rackspace](http://www.rackspace.com/cloud/) remains the winner here at low levels of scale. Evolution from there is probably Amazon.

### Payments provider, In+Out

*  [Amazon FPS](http://aws.amazon.com/fps/). Rejected: US Only (User agreement 2.2.1, 6.2)
*  [Google Checkout](https://checkout.google.com/support/sell/bin/answer.py?answer=134420). Rejected: US+UK Only, no pay out
*  [Braintree](http://www.braintreepayments.com/gateway). Rejected: US Only, no pay out
*  [PaymentExpress](http://www.paymentexpress.com/index.html). Standard merchant gateway. No pay out.
*  [MoneyBookers](http://www.moneybookers.com/app/). Uncertain. Few if any of our target audience have MB accounts. That said, it's not hard to sign up..
*  Paypal. FUUUUUUUUUUUUUU

Retarded location policies by payment providers are extremely frustrating.

### Email delivery services

At this time we're looking at using [Postmark](http://postmarkapp.com/) however previous experience with it has been disappointing,
the delivery times were several minutes and this made it less than useful for notification-style email. Anything that adds that
 kind of latency into an email verification transaction for example is directly getting in the way of a signup.

It seems likely we'll replace it with something else if the delays remain.

### Version control

Well..github, natch.

### Ticket management

Options include Github, [JIRA](http://www.atlassian.com/software/jira/) and [YouTrack](http://www.jetbrains.com/youtrack/). 