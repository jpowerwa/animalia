//  Functions calling animalia APIs

var factUri = '/animals/facts'
var queryUri = '/animals'


function getFormData(formId) {
    var reqData = {}; 
    $.each($('#'+formId).serializeArray(), function (i, input) { 
        reqData[input.name] = input.value; 
    }); 
    return reqData;
};

function addFact(formId) {
    var reqData = getFormData(formId);
    $.ajax({ 
        type: 'POST',
        url: factUri,
        data: JSON.stringify(reqData), 
        contentType: 'application/json, charset=utf-8', 
        success: function(data) { 
            console.log(data); 
        }, 
        error: function(error) { 
            console.log(error); 
        } 
    });
};

function askQuestion(formId) {
    var reqData = getFormData(formId);
    $.ajax({
        type: 'GET',
        url: queryUri + '?q=' + reqData['question'],
        success: function(data) {
            console.log(data);
        },
        error: function(error) {
            console.log(error);
        }
    });
};

function getFact(formId) {
    var reqData = getFormData(formId);
    $.ajax({
        type: 'GET',
        url: factUri + '/' + reqData['fact_id'],
        success: function(data) {
            console.log(data);
        },
        error: function(error) {
            console.log(error);
        }
    });
};

function deleteFact(formId) {
    var reqData = getFormData(formId);
    $.ajax({
        type: 'DELETE',
        url: factUri + '/' + reqData['fact_id'],
        success: function(data) {
            console.log(data);
        },
        error: function(error) {
            console.log(error);
        }
    });
};

