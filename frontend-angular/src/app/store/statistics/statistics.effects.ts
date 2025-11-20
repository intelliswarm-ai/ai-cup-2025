import { Injectable, inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { of } from 'rxjs';
import { map, catchError, switchMap } from 'rxjs/operators';
import { ApiService } from '../../core/services/api.service';
import * as StatisticsActions from './statistics.actions';

@Injectable()
export class StatisticsEffects {
  private actions$ = inject(Actions);
  private apiService = inject(ApiService);

  loadStatistics$ = createEffect(() =>
    this.actions$.pipe(
      ofType(StatisticsActions.loadStatistics),
      switchMap(() =>
        this.apiService.getStatistics().pipe(
          map(statistics => StatisticsActions.loadStatisticsSuccess({ statistics })),
          catchError(error => of(StatisticsActions.loadStatisticsFailure({ error })))
        )
      )
    )
  );
}
