function WebSocketClient(host, port)
{
	this.full_address = host+((port)?":"+port:"");
	this.ws;
	console.log("Connecting to " + this.full_address);
}
WebSocketClient.prototype = {
	connect : function(onMsgFunction, onOpenTrigger)
	{
		var mirror = this;
		this.ws = new WebSocket("ws://"+this.full_address);
		this.ws.onopen = function(i) {
			console.log("Connection open to " + mirror.full_address);
			$(document).trigger(onOpenTrigger);
		}
		this.ws.onclose = function(i){ console.log("Disconnected from " + mirror.full_address); chat.disconnect(); }
		this.ws.onerror = function(e){ console.log(e.data); }
		this.ws.onmessage = onMsgFunction;
	},
	
	send : function(msg){ console.log('> ' + msg); this.ws.send(msg); },
	disconnect : function(){ this.ws.close(); }
}
