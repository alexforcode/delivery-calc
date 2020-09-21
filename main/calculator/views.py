from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import CalculatorForm

from .calculation.calc import Calculator


def get_delivery_info(cleaned_data):

    if not cleaned_data['volume']:
        length = cleaned_data['length']
        width = cleaned_data['width']
        height = cleaned_data['height']
        volume = round(length * width * height, 4)
    else:
        volume = cleaned_data['volume']
        length, width, height = (round(pow(volume, 1 / 3), 2),) * 3

    info = {
        'derival_city': cleaned_data['derival_city'],
        'arrival_city': cleaned_data['arrival_city'],
        'produce_date': '',
        'cargo': {
            'length': length,
            'width': width,
            'height': height,
            'weight': cleaned_data['weight'],
            'volume': volume
        }
    }

    return info


@login_required
def index(request):
    if request.method == 'POST':
        form = CalculatorForm(request.POST)
        if form.is_valid():
            info = get_delivery_info(form.cleaned_data)
            calculator = Calculator(info)
            results = calculator.calculate()
            context = {
                'form': form,
                'results': results
            }
    else:
        form = CalculatorForm()
        context = {'form': form}

    return render(request, 'calculator/index.html', context)
