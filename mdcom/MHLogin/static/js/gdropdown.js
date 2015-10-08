

/************
 Classes to set up the drop-down control
 ************/
function listButton(options)
{
    var control = document.createElement('DIV');
    control.className = "dropDownItemDiv";
    control.title = options.title;
    control.id = options.id;
    control.innerHTML = options.name;
    google.maps.event.addDomListener(control, 'click', options.action);
    return control;
}

function listCheckbox(options)
{
    //first make the outer container
    var container = document.createElement('DIV');
    container.className = "checkboxContainer";
    container.title = (options.title != null) ? options.title : "";
    container.id = "checkbox" + options.id;

    var span = document.createElement('SPAN');
    span.role = "checkbox";
    span.className = "checkboxSpan";

    var bDiv = document.createElement('DIV');
    bDiv.className = "blankDiv";
    bDiv.id = options.id;

    var image = document.createElement('IMG');
    image.className = "blankImg";
    image.src = "https://maps.gstatic.com/mapfiles/mv/imgs8.png";

    var label = document.createElement('LABEL');
    label.className = "checkboxLabel";
    label.innerHTML = options.label;

    bDiv.appendChild(image);
    span.appendChild(bDiv);
    container.appendChild(span);
    container.appendChild(label);

    google.maps.event.addDomListener(container, 'click', function()
    {
        // if group is non-zero length behave like a radio button group, otherwise regular
        if (options.group)
        {   // turn on the option checkbox
            document.getElementById(bDiv.id).style.display = 'block';
            // turn the rest off if associated with a group
            for (ii = 0; ii < options.group.length; ii++)
            {
                document.getElementById(options.group[ii]).style.display = 'none';
            }
        }
        else
        {   // toggle the checkbox on/off
            (document.getElementById(bDiv.id).style.display == 'block') ? document
                    .getElementById(bDiv.id).style.display = 'none' : document
                    .getElementById(bDiv.id).style.display = 'block';
        }
        isChecked = (document.getElementById(bDiv.id).style.display == 'block') ? true : false;        
        options.action(isChecked);
    });
    return container;
}

function listSeparator(options)
{
    var sep = document.createElement('DIV');
    sep.className = "separatorDiv";
    sep.id = options.id;
    return sep;
}

function listDropDown(options)
{
    var container = document.createElement('DIV');
    container.className = 'container';
    container.id = "dropdownlist" + options.id;

    var control = document.createElement('DIV');
    control.className = 'dropDownControl';
    control.style.backgroundColor = 'white';
    control.style.borderStyle = 'solid';
    control.style.borderWidth = '1px';
    control.style.cursor = 'pointer';
    control.style.textAlign = 'center';
    control.style.margin = options.margin;
    control.title = options.title;
    control.innerHTML = '<b>' + options.name + '</b>';
    
    var arrow = document.createElement('IMG');
    arrow.src = "https://maps.gstatic.com/mapfiles/arrow-down.png";
    arrow.className = 'dropDownArrow';
    
    control.appendChild(arrow);
    container.appendChild(control);
    container.appendChild(options.dropDown);

    google.maps.event.addDomListener(container, 'click', function()
    {   // toggle list drop down on/off
        id = options.dropDown.id;
        (document.getElementById(id).style.display == 'block') ? 
                document.getElementById(id).style.display = 'none' :
                document.getElementById(id).style.display = 'block';
    });
    return container;
}

function dropDownOptionsDiv(options)
{
    var container = document.createElement('DIV');
    container.className = "dropDownOptionsDiv";
    container.id = options.id;

    for (i = 0; i < options.items.length; i++)
        container.appendChild(options.items[i]);

    return container;
}

/************
 Simple Button Control
 ************/
function buttonControl(options)
{
    // Set CSS for the control border
    var button = document.createElement('div'); 
    button.style.backgroundColor = 'white';
    button.style.borderStyle = 'solid';
    button.style.borderWidth = '1px';
    button.style.cursor = 'pointer';
    button.style.textAlign = 'center';
    button.style.margin = options.margin;
    button.title = 'Click to set the map to Home';

    // Set CSS for the control interior
    var buttonText = document.createElement('div');
    buttonText.style.fontFamily = 'Arial,sans-serif';
    buttonText.style.fontSize = '12px';
    buttonText.style.paddingLeft = '4px';
    buttonText.style.paddingRight = '4px';
    buttonText.innerHTML = '<b>' + options.name + '</b>';
    button.appendChild(buttonText);

    // When the button is clicked take action by calling options.action function
    google.maps.event.addDomListener(button, 'click', options.action);

    return button;
}

