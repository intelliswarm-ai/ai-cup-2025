import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class PageStateService {
  private lastUpdateSubject = new BehaviorSubject<string>('');
  public lastUpdate$: Observable<string> = this.lastUpdateSubject.asObservable();

  setLastUpdate(timestamp: string): void {
    this.lastUpdateSubject.next(timestamp);
  }

  clearLastUpdate(): void {
    this.lastUpdateSubject.next('');
  }
}
