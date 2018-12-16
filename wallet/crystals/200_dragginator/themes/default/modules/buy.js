<script>
function send(address, amount, operation, data ){
    enabled = true;
    $.get('/transactions/sendpop?recipient='+address+'&amount='+amount+"&data="+data+"&operation="+operation,function(page){
        $("#payment_window").html(page);
        $("#payment_window").modal("show");
        fees = 0.01+0.00001*data.length
        $("#fees").val(fees);
        $("#total").val(amount + fees);
        
        });
    }

function confirmed(){
    if(enabled){
        enabled = false;
        $("#payment_window").css({"cursor":"wait"});
        $("#send_button").prop("disabled",true);

        address = $("#recipient").val();
        data = $("#data").val();
        amount = $("#amount").val();
        operation = $("#operation").val();

        $.get('/transactions/confirmpop?recipient='+address+'&amount='+amount+"&data="+data+"&operation="+operation,function(page){
            $("#payment_window").html(page);
            $("#payment_window").css({"cursor":"context-menu"});
            //$("#payment_window").modal("show");
        });

    }
}


</script>
