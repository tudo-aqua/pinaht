from abc import ABC, abstractmethod


class Event:
    pass


class Observer(ABC):
    def __init__(self, **kwargs):
        super(Observer, self).__init__(**kwargs)

    @abstractmethod
    def notify(self, observable, event: Event):
        raise NotImplementedError()


class Observable(ABC):
    def __init__(self, **kwargs):
        super(Observable, self).__init__(**kwargs)
        self.observers = []

    def register(self, observer: Observer):
        if observer not in self.observers:
            self.observers.append(observer)

    def remove(self, observer: Observer):
        if observer in self.observers:
            self.observers.remove(observer)

    def notify_all(self, event: Event):
        for observer in self.observers:
            observer.notify(self, event)
