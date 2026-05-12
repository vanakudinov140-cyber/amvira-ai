import { Global, Module } from '@nestjs/common';
import { BookingsModule } from '../../modules/bookings/bookings.module';
import { ClientsModule } from '../../modules/clients/clients.module';
import { YclientsHttpClient } from '../../shared/integrations/yclients/client/yclients-http.client';
import { YclientsReadThroughCacheService } from '../../shared/integrations/yclients/cache/yclients-read-through-cache.service';
import { YclientsCompanyRestAdapter } from '../../shared/integrations/yclients/adapters/yclients-company-rest.adapter';
import { YclientsCatalogService } from '../../shared/integrations/yclients/services/yclients-catalog.service';
import { YclientsStaffService } from '../../shared/integrations/yclients/services/yclients-staff.service';
import { YclientsAvailabilityService } from '../../shared/integrations/yclients/services/yclients-availability.service';
import { YclientsBookingService } from '../../shared/integrations/yclients/services/yclients-booking.service';
import { YclientsCustomerService } from '../../shared/integrations/yclients/services/yclients-customer.service';
import { YclientsBookingSyncCoordinator } from '../../shared/integrations/yclients/services/yclients-booking-sync.coordinator';

@Global()
@Module({
  imports: [BookingsModule, ClientsModule],
  providers: [
    YclientsHttpClient,
    YclientsReadThroughCacheService,
    YclientsCompanyRestAdapter,
    YclientsCatalogService,
    YclientsStaffService,
    YclientsAvailabilityService,
    YclientsBookingService,
    YclientsCustomerService,
    YclientsBookingSyncCoordinator,
  ],
  exports: [
    YclientsCatalogService,
    YclientsStaffService,
    YclientsAvailabilityService,
    YclientsBookingService,
    YclientsCustomerService,
    YclientsBookingSyncCoordinator,
  ],
})
export class YclientsModule {}
