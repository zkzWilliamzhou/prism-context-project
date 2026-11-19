# Architecture reference

## Dependency categories

1. **In-process pure computation.** No I/O, in-memory state. Always
   deepenable: merge the modules and test directly.
2. **Local-substitutable.** Dependencies with a local test stand-in (in-memory
   filesystem, PGLite). Deepenable if the substitute exists.
3. **Remote but owned (ports & adapters).** Your own services across a network
   boundary. Define a port at the module boundary; the deep module owns the
   logic.
4. **Remote and unowned.** Third-party services. Keep an adapter at the seam;
   do not pretend the deep module controls the network.

## Deletion test

Ask of every shallow module: if deleted, does complexity concentrate into a
deeper module with a smaller interface, or do we merely move the same
complexity into a new file? Only the first is a deepening opportunity.

## RFC template

```markdown
# RFC: <deepening candidate>

## Friction
<What was hard to understand or test? Use module/interface/seam vocabulary.>

## Cluster
<Files and concepts involved.>

## Dependency category
<1-4 from above.>

## Proposed interface
<1-3 entry points. Show a caller example.>

## Complexity hidden
<What the caller no longer needs to know.>

## Test impact
<Which existing tests become boundary tests; which are deleted.>

## Behavior-preservation gate
<Golden hashes / commands that must remain byte-identical.>

## Trade-offs
<What gets worse.>

## Decision
<Accepted / deferred / rejected, owner, revisit trigger.>
```
