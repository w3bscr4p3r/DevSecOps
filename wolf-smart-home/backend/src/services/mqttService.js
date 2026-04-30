const mqtt = require('mqtt');
const { mqttUrl } = require('../config/env');
const client = mqtt.connect(mqttUrl);
client.on('connect', ()=>{console.log('MQTT conectado'); client.subscribe('home/+/+');});
client.on('message', (topic, payload)=> console.log('MQTT', topic, payload.toString()));
module.exports = { publish: (topic, message)=>client.publish(topic, message), client };
