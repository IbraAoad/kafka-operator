# How to upgrade between minor versions

Charm upgrades allow admins to upgrade both operator code (e.g. the revision used by the charm) and/or the workload version. Note that since the charm code pins a particular version of the workload, a charm upgrade may or may not involve also a workload version upgrade. In general, the following guide only applies for in-place upgrades that involve (at most) minor version upgrade of Kafka workload, e.g. between Kafka 3.4.x to 3.5.x. Major workload upgrades are generally **NOT SUPPORTED**, and they should be carried out using full cluster to cluster migrations. Please refer to the how-to guide about cluster migration [here](/t/charmed-kafka-how-to-cluster-migration/10951) for more information on how this can be achieved.

Perform other extraordinary operations on the Kafka cluster while upgrading is not supported. As an examples, these may be (but not limited to) the following:
1. Adding or removing units
2. Creating or destroying new relations
3. Changes in workload configuration
4. Upgrading other connected applications (e.g. ZooKeeper)

The concurrency with other operations is not supported, and it can lead the cluster into inconsistent states.

## Minor upgrade process overview

When performing an in-place upgrade process, the full process is composed by the following high-level steps:

1. **Collect** all necessary pre-upgrade information, necessary for a rollback (if ever needed)
2. **Prepare** the charm for the in-place upgrade, by running some preparatory tasks 
3. **Upgrade** the charm and/or the workload. Once started, all units in a cluster will refresh the charm code and undergo a workload restart/update. The upgrade will be aborted if the unit upgrade has failed, requiring the admin user to rollback.
4. **Post-upgrade checks** to make sure all units are in the proper state and the cluster is healthy.

## Step 1: Collect

The first step is to record the revisions of the running application, as a safety measure for a rollback action if needed. To accomplish this, simply run the `juju status` command and look for the revisions of the deployed Kafka and Zookeeper applications. You can also retrieve this with the following command (that requires [`yq`](https://snapcraft.io/install/yq/ubuntu) to be installed):

```shell
KAFKA_CHARM_REVISION=$(juju status --format json | yq .applications.<KAFKA_APP_NAME>.charm-rev)
ZOOKEEPER_CHARM_REVISION=$(juju status --format json | yq .applications.<ZOOKEEPER_APP_NAME>.charm-rev)
```

Please fill `<KAFKA_APP_NAME>` and `<ZOOKEEPER_APP_NAME>}` placeholder appropriately, e.g. `kafka` and `zookeeper`.

## Step 2: Prepare

Before upgrading, the charm needs to perform some preparatory tasks to define the upgrade plan.  
To do so, run the `pre-upgrade-check` action against the leader unit:

```shell
juju run-action kafka/leader pre-upgrade-check --wait
```

Make sure that the output of the action is successful, e.g. the output should read:

```shell
unit-kafka-0:
  ...
  results: {}
  status: completed
  ...
```

> Note that you won't be able to upgrade successfully unless you complete successfully this action. 
The action will also configure the charm to minimize high-availability reduction and ensure a safe upgrade process. After successful execution, the charm is ready to be upgraded.

## Step 3: Upgrade

Use the [`juju refresh`](https://juju.is/docs/juju/juju-refresh) command to trigger the charm upgrade process.
Note that the upgrade can be performed against:

* selected channel/track, therefore upgrading to the latest revision published on that track
```shell
juju refresh kafka --channel 3/edge
```
* selected revision
```shell
juju refresh kafka --revision=<REVISION>
```
* a local charm file
```shell
juju refresh kafka --path ./kafka_ubuntu-22.04-amd64.charm
```

When issuing the commands, all units will refresh (i.e. receive new charm content), and the upgrade charm event will be fired. The charm will take care of executing a update (if required) and a restart of the workload one unit at the time to not lose high-availability. 

The upgrade process can be monitored using `juju status` command, where the message of the units will provide information about which units have been upgraded already, which unit is currently upgrading and which units are waiting for the upgrade to be triggered, as shown below: 

```shell
...

App        Version  Status  Scale  Charm      Channel  Rev  Exposed  Message
kafka               active      3  kafka      3/edge   135  no

Unit          Workload  Agent  Machine  Public address  Ports  Message
...
kafka/0       active    idle   3        10.193.41.131          Other units upgrading first...
kafka/1*      active    idle   4        10.193.41.109          Upgrading...
kafka/2       active    idle   5        10.193.41.221          Upgrade completed
...

```

### Failing upgrade

Before upgrading the unit, the charm will check whether the upgrade can be performed, e.g. this may mean:
1. Checking that the upgrade from the previous charm revision and Kafka version is allowed
2. Checking that other external applications that Kafka depends on (e.g. Zookeeper) are running the correct version

Note that these checks are only possible after a refresh of the charm code, and therefore cannot be done upfront (e.g. during the `pre-upgrade-checks` action).
If some of these checks fail, the upgrade will be aborted. When this happens, the workload may still be operating (as only the operator may have failed) but we recommend to rollback the upgrade as soon as possible. 

In order to roll back the upgrade, re-run steps 2 and 3, using the revision taken in step 1, i.e.

```shell
juju run-action kafka/leader pre-upgrade-check --wait

juju refresh kafka --revision=${KAFKA_CHARM_REVISION}
```

We strongly recommend to also retrieve the full set of logs with `juju debug-log`, to extract insights on why the upgrade failed. 

## Kafka and Zookeeper combined upgrades

Although the following guide will focus on upgrading Kafka, the same process can also be applied to Zookeeper, should you need to upgrade this component as well. If Kafka and Zookeeper charms need both to be upgraded, we recommend you to start the upgrade from the Zookeeper cluster. As outlined above, the two upgrades should **NEVER** be done concurrently.