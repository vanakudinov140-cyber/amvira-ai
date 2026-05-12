import {
  ArgumentsHost,
  Catch,
  ExceptionFilter,
  HttpException,
  HttpStatus,
  Injectable,
} from '@nestjs/common';
import type { Response } from 'express';
import type { OperatorApiErrorBodyV1 } from './operator-api-envelope.types';

@Injectable()
@Catch()
export class OperatorApiExceptionFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost): void {
    const ctx = host.switchToHttp();
    const res = ctx.getResponse<Response>();

    if (exception instanceof HttpException) {
      const status = exception.getStatus();
      const resBody = exception.getResponse();
      const message =
        typeof resBody === 'string'
          ? resBody
          : typeof resBody === 'object' &&
              resBody !== null &&
              'message' in resBody &&
              typeof (resBody as { message: unknown }).message === 'string'
            ? (resBody as { message: string }).message
            : exception.message;
      const body: OperatorApiErrorBodyV1 = {
        errorVersion: 'operator_api_error@v1',
        status,
        code: `http_${status}`,
        message,
      };
      res.status(status).json(body);
      return;
    }

    const body: OperatorApiErrorBodyV1 = {
      errorVersion: 'operator_api_error@v1',
      status: HttpStatus.INTERNAL_SERVER_ERROR,
      code: 'internal_error',
      message: 'Unexpected operator API error',
      details: [
        exception instanceof Error ? exception.message : String(exception),
      ],
    };
    res.status(HttpStatus.INTERNAL_SERVER_ERROR).json(body);
  }
}
